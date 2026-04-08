import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ETSY_API_KEY = os.environ.get("ETSY_API_KEY")
ETSY_SECRET = os.environ.get("ETSY_SECRET")
ETSY_SHOP_ID = os.environ.get("ETSY_SHOP_ID")
ETSY_ACCESS_TOKEN = os.environ.get("ETSY_ACCESS_TOKEN")

def post_listing_to_etsy(listing: dict) -> dict:
    """Postet ein generiertes Listing direkt auf Etsy"""
    
    headers = {
        "x-api-key": ETSY_API_KEY,
        "Authorization": f"Bearer {ETSY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": listing.get("title", "")[:140],
        "description": listing.get("description", ""),
        "price": listing.get("price", 29.90),
        "quantity": 1,
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "taxonomy_id": 68887515,
        "tags": listing.get("tags", [])[:13],
        "state": "draft"
    }
    
    url = f"https://openapi.etsy.com/v3/application/shops/{ETSY_SHOP_ID}/listings"
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 201:
        return {"success": True, "listing_id": response.json().get("listing_id")}
    else:
        return {"success": False, "error": response.text}
