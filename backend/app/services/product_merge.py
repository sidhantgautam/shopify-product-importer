import math
from typing import Dict, Any
from app.shopify.client import ShopifyClient


class ProductMergeService:
    def __init__(self):
        self.client = ShopifyClient()

    def find_existing_product(self, product: Dict[str, Any]) -> Dict | None:
        """
        Find existing Shopify product using priority:
        1. Product ID
        2. Handle
        3. (Optional) Title
        """

        product_id = product.get("id")

        # Lookup by Product ID (only if valid)
        if product_id and str(product_id).lower() != "nan":
            existing = self.client.get_product_by_id(product_id)
            if existing:
                return existing

        # Lookup by Handle
        if product.get("handle"):
            existing = self.client.get_product_by_handle(product["handle"])
            if existing:
                return existing
        return None

    def merge_product_fields(self, existing: Dict, incoming: Dict) -> Dict:

        update = {}

        for field in ["title", "body_html", "vendor", "product_type", "tags"]:
            if incoming.get(field) is not None:
                update[field] = incoming[field]

        return update
    
    def find_existing_variant(self, shopify_variants, incoming_variant):

        # Match by Variant ID
        if incoming_variant.get("id"):
            for v in shopify_variants:
                if v.get("id") == incoming_variant["id"]:
                    return v

        # Match by SKU
        if incoming_variant.get("sku"):
            for v in shopify_variants:
                if v.get("sku") == incoming_variant["sku"]:
                    return v

        return None



    def merge_variant_fields(self, incoming: Dict[str, Any]) -> Dict[str, Any]:

        payload: Dict[str, Any] = {}

        # SKU
        if incoming.get("sku"):
            payload["sku"] = incoming["sku"]

        # PRICE 
        price = incoming.get("price")
        if price is not None and not (isinstance(price, float) and math.isnan(price)):
            payload["price"] = price

        # COMPARE AT PRICE
        compare_at = incoming.get("compare_at_price")
        if compare_at is not None and not (isinstance(compare_at, float) and math.isnan(compare_at)):
            payload["compare_at_price"] = compare_at

        # WEIGHT
        weight = incoming.get("weight")
        if weight is not None and not (isinstance(weight, float) and math.isnan(weight)):
            payload["weight"] = weight

        # INVENTORY
        inventory = incoming.get("inventory_qty")
        if inventory is not None:
            payload["inventory_quantity"] = inventory

        return payload

    def process_variants(self, shopify_product: dict, incoming_variants: list):
        product_id = shopify_product["id"]
        shopify_variants = self.client.get_variants_for_product(product_id)

        shopify_sku_map = {}
        for v in shopify_variants:
            sku = v.get("sku")
            if sku:
                shopify_sku_map[sku] = v["id"]

        results = {
            "created": [],
            "updated": [],
            "skipped": [],
            "errors": [],
        }


        for incoming in incoming_variants:
            sku = incoming.get("sku")
            existing = self.find_existing_variant(shopify_variants, incoming)

            if sku in shopify_sku_map:
                shopify_variant_id = shopify_sku_map[sku]

                if not existing or existing["id"] != shopify_variant_id:
                    results["skipped"].append(sku)
                    results["errors"].append({
                        "sku": sku,
                        "error": "Duplicate SKU already exists in Shopify",
                    })
                    continue

            payload = self.merge_variant_fields(incoming)

            options = incoming.get("options", {})
            option_values = list(options.values())

            if option_values:
                payload["option1"] = option_values[0]
                if len(option_values) > 1:
                    payload["option2"] = option_values[1]
                if len(option_values) > 2:
                    payload["option3"] = option_values[2]
            else:
                payload["option1"] = "Default"


            if existing:
                self.client.update_variant(existing["id"], payload)
                results["updated"].append(sku)
            else:
                self.client.create_variant(product_id, payload)
                results["created"].append(sku)

        return results


    def build_shopify_product_payload(self, product: dict) -> dict:

        payload = {}

        title = product.get("title")
        handle = product.get("handle")

        if not title:
            title = handle

        payload["title"] = title

        if handle is not None:
            payload["handle"] = handle

        for field in ["body_html", "vendor", "product_type"]:
            if product.get(field) is not None:
                payload[field] = product[field]

        if product.get("tags"):
            payload["tags"] = ",".join(product["tags"])

        return payload
