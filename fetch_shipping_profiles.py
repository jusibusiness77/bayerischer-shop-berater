"""Listet die Shipping Profiles von Mamas Etsy Shop auf."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

API_KEY = os.environ.get("ETSY_API_KEY")
SHARED_SECRET = os.environ.get("ETSY_SHARED_SECRET")
ACCESS_TOKEN = os.environ.get("ETSY_ACCESS_TOKEN")
SHOP_ID = os.environ.get("ETSY_SHOP_ID")


def main() -> int:
    for name, value in [
        ("ETSY_API_KEY", API_KEY),
        ("ETSY_SHARED_SECRET", SHARED_SECRET),
        ("ETSY_ACCESS_TOKEN", ACCESS_TOKEN),
        ("ETSY_SHOP_ID", SHOP_ID),
    ]:
        if not value:
            print(f"FEHLER: {name} fehlt in .env", file=sys.stderr)
            return 1

    url = f"https://openapi.etsy.com/v3/application/shops/{SHOP_ID}/shipping-profiles"
    print(f"GET {url}")
    r = requests.get(
        url,
        headers={
            "x-api-key": f"{API_KEY}:{SHARED_SECRET}",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        },
        timeout=30,
    )
    print(f"HTTP {r.status_code}")

    if r.status_code != 200:
        print(f"Antwort: {r.text}", file=sys.stderr)
        return 1

    data = r.json()
    profiles = data.get("results", [])

    if not profiles:
        print("\nKeine Shipping Profiles gefunden. Mama muss in Etsy eines anlegen.")
        return 1

    print(f"\n{len(profiles)} Shipping Profile gefunden:\n")
    for p in profiles:
        primary = " (PRIMARY)" if p.get("is_default") else ""
        print(f"  {p.get('shipping_profile_id')}  {p.get('title')}{primary}")
        print(f"    Origin: {p.get('origin_country_iso')}  Bearbeitung: "
              f"{p.get('min_processing_days')}-{p.get('max_processing_days')} Tage")

    primary = next((p for p in profiles if p.get("is_default")), profiles[0])
    print(f"\nVorschlag fuer ETSY_SHIPPING_PROFILE_ID: {primary.get('shipping_profile_id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
