import httpx
from typing import Dict

from app.core.config import (
    SHOPIFY_STORE_URL,
    SHOPIFY_ACCESS_TOKEN,
    SHOPIFY_API_VERSION,
)

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{SHOPIFY_API_VERSION}"

HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json",
}


class ShopifyClient:
    def __init__(self):
        self.client = httpx.Client(headers=HEADERS, timeout=30)


    def get_products(self, limit=5):
        url = f"{BASE_URL}/products.json"
        response = self.client.get(url, params={"limit": limit})
        response.raise_for_status()
        return response.json()

    def get_product_by_id(self, product_id: int):
        url = f"{BASE_URL}/products/{product_id}.json"
        response = self.client.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("product")

    def get_product_by_handle(self, handle: str):
        url = f"{BASE_URL}/products.json"
        response = self.client.get(url, params={"handle": handle})
        response.raise_for_status()
        products = response.json().get("products", [])
        return products[0] if products else None

    def create_product(self, payload: dict):
        url = f"{BASE_URL}/products.json"
        response = self.client.post(url, json={"product": payload})
        response.raise_for_status()
        return response.json().get("product")

    def update_product(self, product_id: int, payload: dict):
        url = f"{BASE_URL}/products/{product_id}.json"
        response = self.client.put(url, json={"product": payload})
        response.raise_for_status()
        return response.json().get("product")



    def get_variants_for_product(self, product_id: int):
        url = f"{BASE_URL}/products/{product_id}.json"
        response = self.client.get(url)
        response.raise_for_status()
        product = response.json().get("product", {})
        return product.get("variants", [])

    def update_variant(self, variant_id: int, payload: dict):
        url = f"{BASE_URL}/variants/{variant_id}.json"
        response = self.client.put(url, json={"variant": payload})
        response.raise_for_status()
        return response.json().get("variant")


    def create_variant(self, product_id: int, payload: dict):
        url = f"{BASE_URL}/products/{product_id}/variants.json"
        response = self.client.post(url, json={"variant": payload})
        response.raise_for_status()
        return response.json().get("variant")
