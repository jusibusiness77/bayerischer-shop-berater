"""Postet ein generiertes Listing als Draft auf Etsy (Etsy Open API v3)."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _env(key: str) -> str | None:
    load_dotenv(ENV_PATH, override=True)
    return os.environ.get(key)


def _decode_image(image_data: str) -> tuple[bytes, str]:
    """Akzeptiert data-URI oder reines base64. Gibt (bytes, mime) zurueck."""
    mime = "image/jpeg"
    encoded = image_data
    if image_data.startswith("data:"):
        header, encoded = image_data.split(",", 1)
        if ";" in header:
            mime = header.split(":", 1)[1].split(";", 1)[0] or mime
    return base64.b64decode(encoded), mime


def _upload_image(
    shop_id: str,
    listing_id: int,
    image_data: str,
    image_name: str | None,
    rank: int,
    headers: dict,
) -> dict:
    try:
        image_bytes, mime = _decode_image(image_data)
    except Exception as exc:
        return {"uploaded": False, "rank": rank, "error": f"Bild konnte nicht dekodiert werden: {exc}"}

    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(mime, ".jpg")
    filename = image_name or f"foto{rank}{ext}"

    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images"
    files = {"image": (filename, image_bytes, mime)}
    data = {"rank": rank, "overwrite": "true"}

    upload_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}

    try:
        r = requests.post(url, headers=upload_headers, files=files, data=data, timeout=60)
    except requests.RequestException as exc:
        return {"uploaded": False, "rank": rank, "error": f"Netzwerkfehler beim Bild-Upload: {exc}"}

    if r.status_code in (200, 201):
        return {"uploaded": True, "rank": rank, "listing_image_id": r.json().get("listing_image_id")}

    return {"uploaded": False, "rank": rank, "error": f"Etsy {r.status_code}: {r.text}"}


def post_listing_to_etsy(
    listing: dict,
    price: float | None = None,
    images: list[dict] | None = None,
) -> dict:
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
        "when_made": "2020_2026",
        "taxonomy_id": 1062,
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
        result = {
            "success": True,
            "listing_id": listing_id,
            "url": f"https://www.etsy.com/your/shops/me/tools/listings/{listing_id}" if listing_id else None,
        }

        if listing_id and images:
            uploads = []
            for i, img in enumerate(images, start=1):
                data = img.get("data") if isinstance(img, dict) else None
                name = img.get("name") if isinstance(img, dict) else None
                if not data:
                    uploads.append({"uploaded": False, "rank": i, "error": "Kein Bilddaten-Feld"})
                    continue
                uploads.append(_upload_image(shop_id, listing_id, data, name, i, headers))

            successful = sum(1 for u in uploads if u.get("uploaded"))
            result["images_total"] = len(uploads)
            result["images_uploaded"] = successful
            errors = [u.get("error") for u in uploads if not u.get("uploaded") and u.get("error")]
            if errors:
                result["image_errors"] = errors
        elif listing_id:
            result["images_total"] = 0
            result["images_uploaded"] = 0
            result["image_errors"] = ["Keine Bilder mitgesendet."]

        return result

    return {"success": False, "error": f"Etsy {response.status_code}: {response.text}"}
