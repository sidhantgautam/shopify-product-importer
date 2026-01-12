import math

from typing import Dict, Any



def normalize_row(row: Dict[str, Any], row_number: int) -> Dict[str, Any]:

    raw_id = row.get("ID")

    product_id = None
    if raw_id is not None and not (isinstance(raw_id, float) and math.isnan(raw_id)):
        product_id = str(int(raw_id)) if isinstance(raw_id, (int, float)) else str(raw_id)


    product = {
        "id": product_id,
        "handle": _to_str(row.get("Handle")),
        "title": _to_str(row.get("Title")),
        "body_html": _to_str(row.get("Body (HTML)")),
        "vendor": _to_str(row.get("Vendor")),
        "product_type": _to_str(row.get("Product Type")),
        "tags": _parse_tags(row.get("Tags")),
    }


    raw_weight = row.get("Variant Weight")

    weight = None
    if raw_weight is not None:
        try:
            w = float(raw_weight)
            if not math.isnan(w):
                weight = w
        except (ValueError, TypeError):
            pass

    variant = {
        "id": row.get("Variant ID"),
        "sku": _to_str(row.get("Variant SKU")),
        "price": _to_float(row.get("Variant Price")),
        "compare_at_price": _to_float(row.get("Variant Compare At Price")),
        "inventory_qty": _to_int(row.get("Variant Inventory Qty")),
        "weight": float(raw_weight) if raw_weight is not None else None,
        "options": _parse_options(row),
    }


    return {
        "product": product,
        "variant": variant,
    }


def _parse_tags(value):
    if not value:
        return []
    return [tag.strip() for tag in str(value).split(",") if tag.strip()]


def _parse_options(row: Dict[str, Any]) -> Dict[str, str]:
    options = {}

    for i in range(1, 4):
        name = row.get(f"Option{i} Name")
        value = row.get(f"Option{i} Value")

        if name and value:
            options[str(name)] = str(value)

    return options


def _to_float(value):
    try:
        if value is None:
            return None
        value = float(value)
        if math.isnan(value):
            return None
        return value
    except (ValueError, TypeError):
        return None


def _to_int(value):
    try:
        if value is None:
            return None
        value = int(value)
        return value
    except (ValueError, TypeError):
        return None

def _to_str(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    value = str(value).strip()
    return value if value else None