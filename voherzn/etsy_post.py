"""Postet ein generiertes Listing als Draft auf Etsy (Etsy Open API v3)."""

from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _env(key: str) -> str | None:
    load_dotenv(ENV_PATH, override=True)
    return os.environ.get(key)


def post_listing_to_etsy(listing: dict, price: float | None = None) -> dict:
    api_key = _env("ETSY_API_KEY")
    shared_secret = _env("ETSY_SHARED_SECRET")
    access_token = _env("ETSY_ACCESS_TOKEN")
    shop_id = _env("ETSY_SHOP_ID")
    shipping_profile_id = _env("ETSY_SHIPPING_PROFILE_ID")
    readiness_state_id = _env("ETSY_READINESS_STATE_ID")

    if not api_key:
        return {"success": False, "error": "ETSY_API_KEY fehlt in .env"}
    if not shared_secret:
        return {"success": False, "error": "ETSY_SHARED_SECRET fehlt in .env"}
    if not access_token:
        return {"success": False, "error": "Nicht authentifiziert. Bitte zuerst /auth/etsy aufrufen.", "needs_auth": True}
    if not shop_id:
        return {"success": False, "error": "ETSY_SHOP_ID fehlt - Auth wiederholen."}
    if not shipping_profile_id:
        return {"success": False, "error": "ETSY_SHIPPING_PROFILE_ID fehlt in .env"}
    if not readiness_state_id:
        return {"success": False, "error": "ETSY_READINESS_STATE_ID fehlt in .env"}

    headers = {
        "x-api-key": f"{api_key}:{shared_secret}",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        listing_price = float(price) if price else 29.90
    except (TypeError, ValueError):
        listing_price = 29.90

    payload = {
        "quantity": 1,
        "title": (listing.get("title") or "")[:140],
        "description": listing.get("description") or "",
        "price": listing_price,
        "who_made": "i_did",
        "when_made": "made_to_order",
        "taxonomy_id": 68887515,
        "shipping_profile_id": int(shipping_profile_id),
        "readiness_state_id": int(readiness_state_id),
        "tags": (listing.get("tags") or [])[:13],
        "state": "draft",
    }

    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings"
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        return {"success": False, "error": f"Netzwerkfehler: {exc}"}

    if response.status_code == 401:
        return {"success": False, "error": "Token abgelaufen. Bitte erneut /auth/etsy aufrufen.", "needs_auth": True}

    if response.status_code in (200, 201):
        body = response.json()
        listing_id = body.get("listing_id")
        return {
            "success": True,
            "listing_id": listing_id,
            "url": f"https://www.etsy.com/your/shops/me/tools/listings/{listing_id}" if listing_id else None,
        }

    return {"success": False, "error": f"Etsy {response.status_code}: {response.text}"}
