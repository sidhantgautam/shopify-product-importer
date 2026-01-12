from typing import List, Dict, Any, Tuple

def validate_products(
    products: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

    valid_products = []
    errors = []

    for product in products:
        product_errors = []

        handle = product.get("handle")
        title = product.get("title")

        # Product-level validation
        if not handle and not title:
            product_errors.append(
                "Product must have at least Handle or Title"
            )

        # Variant-level validation 
        valid_variants = []
        for idx, variant in enumerate(product.get("variants", [])):
            if not (variant.get("id") or variant.get("sku")):
                product_errors.append(
                    f"Variant at index {idx} must have Variant ID or SKU"
                )
            else:
                valid_variants.append(variant)

        # Collect results
        if product_errors:
            errors.append({
                "product": handle or title or "Unknown product",
                "errors": product_errors,
            })
        else:
            product["variants"] = valid_variants
            valid_products.append(product)

    return valid_products, errors
