from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
import openpyxl
import json
import io

from app.parser.csv_excel_reader import read_file
from app.parser.normalizer import normalize_row
from app.parser.grouper import group_products
from app.parser.validator import validate_products
from app.services.product_merge import ProductMergeService
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

router = APIRouter(prefix="/import", tags=["Import"])

@router.get("/products/result/{result_id}")
def download_import_result(result_id: str):
    result_path = f"/tmp/import_result_{result_id}.json"

    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result not found")

    with open(result_path, "r") as f:
        row_results = json.load(f)

    wb = Workbook()
    ws = wb.active
    ws.title = "Import Results"

    # Collect all column names dynamically
    all_columns = set()
    for r in row_results:
        all_columns.update((r.get("data") or {}).keys())

    all_columns = list(all_columns)

    # Header
    headers = ["Row"] + list(row_results[0]["data"].keys()) + ["Status", "Error"]
    ws.append(headers)

    # Rows
    for r in row_results:
        row_data = r.get("data", {})
        ws.append(
            [r.get("row")] +
            [row_data.get(h, "") for h in headers[1:-2]] +
            [r.get("status"), r.get("error")]
        )

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=import_results.xlsx",
            "Cache-Control": "no-store",
        }
    )

@router.post("/products")
def import_products(file: UploadFile = File(...)):
    temp_filename = f"/tmp/{uuid.uuid4()}_{file.filename}"

    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Parse file
        rows = read_file(temp_filename)

        row_results = []

        # Normalize
        normalized = []
        row_errors = []


        seen_skus = set()

        for index, row in enumerate(rows, start=2):  # start=2 CSV header is row 1
                try:
                    normalized_row = normalize_row(row, index)

                    sku = normalized_row.get("variant", {}).get("sku")

                    # duplicate SKU inside same import
                    if sku:
                        if sku in seen_skus:
                            row_results.append({
                                "row": index,
                                "status": "skipped",
                                "error": f"Duplicate SKU '{sku}' found in same import. Row skipped.",
                                "data": row,
                                "sku": sku
                            })
                            continue

                    seen_skus.add(sku)

                    normalized.append(normalized_row)

                    row_results.append({
                        "row": index,
                        "sku": sku,
                        "status": "pending",
                        "error": "",
                        "data": row
                    })

                    
                except ValueError as e:
                    row_errors.append({
                        "row": index,
                        "status": "error",
                        "error": str(e)
                    })

        # Group products
        grouped = group_products(normalized)

        # Validate
        valid_products, validation_errors = validate_products(grouped)

        # MERGE validation errors instead of overwriting
        row_errors.extend(validation_errors)

        # if not valid_products:
        if not valid_products and row_errors:
            return {
                "products_created": 0,
                "products_updated": 0,
                "variants_created": 0,
                "variants_updated": 0,
                "errors": row_errors,
            }


        merge_service = ProductMergeService()

        # Summary response
        summary = {
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
            "errors": row_errors, 
        }


        processed_product_ids = set()

        for product in valid_products:

            if not product.get("handle") and not product.get("title"):

                invalid_skus = {v.get("sku") for v in product.get("variants", [])}

                for r in row_results:
                    if r.get("sku") in invalid_skus:
                        r["status"] = "error"
                        r["error"] = "Product must have at least Handle or Title"
                continue 

            existing = merge_service.find_existing_product(product)

            if existing:
                shopify_product = existing
                if existing["id"] not in processed_product_ids:
                    update_payload = merge_service.merge_product_fields(existing, product)
                    if update_payload:
                        merge_service.client.update_product(existing["id"], update_payload)
                        summary["products_updated"] += 1
                    processed_product_ids.add(existing["id"])
            else:
                product_payload = merge_service.build_shopify_product_payload(product)
                shopify_product = merge_service.client.create_product(product_payload)
                summary["products_created"] += 1
                processed_product_ids.add(shopify_product["id"])

            result = merge_service.process_variants(
                shopify_product,
                product.get("variants", [])
            )

            for r in row_results:
                sku = r.get("sku")

                if r["status"] != "pending" or not sku:
                    continue

                if sku in result.get("created", []):
                    r["status"] = "created"

                elif sku in result.get("updated", []):
                    r["status"] = "updated"

                elif sku in result.get("skipped", []):
                    r["status"] = "skipped"

            summary["variants_created"] += len(result["created"])
            summary["variants_updated"] += len(result["updated"])

            for err in result.get("errors", []):
                for r in row_results:
                    if r.get("sku") == err.get("sku"):
                        r["status"] = "error"
                        r["error"] = err["error"]


            summary.setdefault("errors", [])
            summary["errors"].extend(result.get("errors", []))

        result_id = str(uuid.uuid4())
        result_path = f"/tmp/import_result_{result_id}.json"

        with open(result_path, "w") as f:
            json.dump(row_results, f)

        summary["download_id"] = result_id

        return summary

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
