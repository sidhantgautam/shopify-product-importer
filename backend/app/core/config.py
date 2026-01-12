from dotenv import load_dotenv
import os

load_dotenv()

SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    raise RuntimeError("Missing required Shopify configuration")
