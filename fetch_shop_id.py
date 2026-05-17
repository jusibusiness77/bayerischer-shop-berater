"""Holt die numerische Etsy Shop-ID via OAuth und schreibt sie in die .env."""

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


def write_shop_id(shop_id: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith("ETSY_SHOP_ID="):
            lines[i] = f"ETSY_SHOP_ID={shop_id}"
            found = True
            break
    if not found:
        lines.append(f"ETSY_SHOP_ID={shop_id}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not API_KEY:
        print("FEHLER: ETSY_API_KEY fehlt in .env", file=sys.stderr)
        return 1
    if not SHARED_SECRET:
        print("FEHLER: ETSY_SHARED_SECRET fehlt in .env", file=sys.stderr)
        return 1
    if not ACCESS_TOKEN:
        print("FEHLER: ETSY_ACCESS_TOKEN fehlt in .env - erst OAuth durchlaufen.", file=sys.stderr)
        return 1

    user_id = ACCESS_TOKEN.split(".", 1)[0]
    if not user_id.isdigit():
        print(f"FEHLER: Konnte user_id nicht aus Access Token extrahieren: {user_id}", file=sys.stderr)
        return 1

    url = f"https://openapi.etsy.com/v3/application/users/{user_id}/shops"
    x_api_key = f"{API_KEY}:{SHARED_SECRET}"

    print(f"GET {url}")
    r = requests.get(
        url,
        headers={"x-api-key": x_api_key, "Authorization": f"Bearer {ACCESS_TOKEN}"},
        timeout=30,
    )
    print(f"HTTP {r.status_code}")

    if r.status_code != 200:
        print(f"Antwort: {r.text}", file=sys.stderr)
        return 1

    data = r.json()
    shop_id = data.get("shop_id")
    shop_name = data.get("shop_name")

    if not shop_id:
        print(f"Kein shop_id in Antwort: {data}", file=sys.stderr)
        return 1

    print()
    print(f"  Shop:    {shop_name}")
    print(f"  Shop-ID: {shop_id}")
    print()

    write_shop_id(str(shop_id))
    print(f"In .env eingetragen: ETSY_SHOP_ID={shop_id}")
    print(f"Auf Render eintragen: ETSY_SHOP_ID={shop_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
