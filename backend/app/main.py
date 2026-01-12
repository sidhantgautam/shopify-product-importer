import os

from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
from app.shopify.client import ShopifyClient
from app.api.import_products import router as import_router
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

app = FastAPI(title="Shopify Product Import Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(import_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/shopify/test")
def shopify_test():
    client = ShopifyClient()
    return client.get_products()

