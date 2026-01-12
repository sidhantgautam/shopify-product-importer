from typing import List, Dict, Any

def group_products(normalized_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    products_map = {}

    for row in normalized_rows:
        product = row["product"]
        variant = row["variant"]

        product_key = _get_product_key(product)

        if not product_key:
            product_key = f"__invalid__:{id(product)}"

        if product_key not in products_map:
            products_map[product_key] = {
                **product,
                "variants": []
            }

        if variant:
            products_map[product_key]["variants"].append(variant)

    return list(products_map.values())


def _get_product_key(product: Dict[str, Any]) -> str:

    # Determines unique key for a product.
    # Priority: ID > Handle > Title

    if product.get("id"):
        return f"id:{product['id']}"

    if product.get("handle"):
        return f"handle:{product['handle']}"

    if product.get("title"):
        return f"title:{product['title']}"

    return None