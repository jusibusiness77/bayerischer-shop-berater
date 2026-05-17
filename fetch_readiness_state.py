"""Ermittelt die readiness_state_id(s) aus bestehenden Listings von Mamas Shop.

Etsy hat (Stand 2026) keinen dedizierten /readiness-states Endpoint,
deshalb lesen wir die Werte aus den existierenden Listings aus.
"""

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


def fetch(state: str) -> list[dict]:
    url = f"https://openapi.etsy.com/v3/application/shops/{SHOP_ID}/listings/{state}"
    r = requests.get(
        url,
        headers={
            "x-api-key": f"{API_KEY}:{SHARED_SECRET}",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        },
        params={"limit": 50},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"GET {url} -> HTTP {r.status_code}: {r.text}", file=sys.stderr)
        return []
    return r.json().get("results", [])


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

    all_listings: list[dict] = []
    for state in ("active", "draft", "inactive"):
        listings = fetch(state)
        print(f"  {state}: {len(listings)} Listings")
        all_listings.extend(listings)

    if not all_listings:
        print("\nKeine Listings gefunden - Mama muss erst eines in Etsy anlegen.", file=sys.stderr)
        return 1

    seen: dict[int, dict] = {}
    for lst in all_listings:
        rid = lst.get("readiness_state_id")
        if rid and rid not in seen:
            seen[rid] = {
                "readiness_state_id": rid,
                "processing_min": lst.get("processing_min"),
                "processing_max": lst.get("processing_max"),
                "example_listing": lst.get("title"),
            }

    if not seen:
        print("\nKein Listing hatte readiness_state_id gesetzt.", file=sys.stderr)
        return 1

    print(f"\n{len(seen)} eindeutige readiness_state_id(s) gefunden:\n")
    for info in seen.values():
        print(f"  {info['readiness_state_id']}")
        print(f"    Bearbeitungszeit: {info['processing_min']}-{info['processing_max']} Tage")
        print(f"    Beispiel-Listing: {info['example_listing']}")
        print()

    primary = next(iter(seen.values()))
    print(f"Vorschlag fuer ETSY_READINESS_STATE_ID: {primary['readiness_state_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
