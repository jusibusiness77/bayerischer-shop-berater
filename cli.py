"""Vo Herz'n Content Creator — CLI Tool fuer Mama."""

import os
import sys

from voherzn.vision import analyze_photo, analyze_photos, analyze_from_text
from voherzn.season import get_season_context
from voherzn.etsy import generate_listing
from voherzn.instagram import generate_caption, create_post_image
from voherzn.output import OutputManager

HEADER = """
============================================
   Vo Herz'n — Content Creator
============================================
"""

MENU = """
Was moechtest du tun?

1. Einzelnes Produkt (Etsy + Instagram)
2. Mehrere Produkte (Batch, bis zu 10 Fotos)
3. Nur Etsy Listing
4. Nur Instagram Post
5. Beenden
"""

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _clean_path(path: str) -> str:
    return path.strip().strip("'\"")


def _get_product_info() -> dict:
    print("\nWie moechtest du das Produkt beschreiben?")
    print("1. Foto")
    print("2. Textbeschreibung")
    choice = input("\nDeine Wahl (1/2): ").strip()

    if choice == "1":
        raw = input("Dateipfad zum Foto (Drag & Drop moeglich): ")
        path = _clean_path(raw)
        if not os.path.isfile(path):
            print(f"\nDatei nicht gefunden: {path}")
            return {}
        print("\nFoto wird analysiert...")
        product = analyze_photo(path)
    elif choice == "2":
        desc = input("Beschreibe das Produkt: ").strip()
        if not desc:
            print("\nKeine Beschreibung eingegeben.")
            return {}
        print("\nBeschreibung wird analysiert...")
        product = analyze_from_text(desc)
    else:
        print("\nUngueltige Wahl.")
        return {}

    print(f"\nProdukt: {product.get('product_name', '?')}")
    print(f"Kategorie: {product.get('category', '?')}")
    return product


def _print_season_info(season: dict):
    print(f"\nSaison: {season['season']}")
    events = season.get("events", [])
    if events:
        print(f"Aktuelle Anlaesse: {', '.join(events)}")
    else:
        print("Keine besonderen Anlaesse gerade.")


def _format_listing_text(listing: dict) -> str:
    parts = []
    parts.append(f"TITEL:\n{listing.get('title', '')}\n")
    parts.append(f"BESCHREIBUNG:\n{listing.get('description', '')}\n")
    tags = listing.get("tags", [])
    if tags:
        parts.append(f"TAGS:\n{', '.join(tags)}")
    return "\n".join(parts)


def _single_product(mode: str):
    product = _get_product_info()
    if not product:
        return

    season = get_season_context()
    _print_season_info(season)

    out = OutputManager()
    saved = []

    if mode in ("both", "etsy"):
        print("\nEtsy Listing wird erstellt...")
        listing = generate_listing(product, season)
        text = _format_listing_text(listing)
        path = out.save_etsy_listing(product.get("product_name", "produkt"), text)
        saved.append(f"Etsy Listing: {path}")
        print(f"  -> {path}")

    if mode in ("both", "instagram"):
        print("\nInstagram Caption wird erstellt...")
        caption = generate_caption(product, season)
        cap_path = out.save_instagram_caption(product.get("product_name", "produkt"), caption)
        saved.append(f"Instagram Caption: {cap_path}")
        print(f"  -> {cap_path}")

        print("Instagram Bild wird erstellt...")
        short_text = product.get("product_name", "Handgemacht mit Liebe")
        img = create_post_image(short_text)
        img_path = out.save_instagram_image(product.get("product_name", "produkt"), img)
        saved.append(f"Instagram Bild: {img_path}")
        print(f"  -> {img_path}")

    print(f"\nAlle Dateien gespeichert in: {out.root}")


def _batch():
    print("\nOrdnerpfad oder einzelne Dateipfade (kommagetrennt):")
    raw = input("> ").strip()
    raw = _clean_path(raw)

    photo_paths = []

    if os.path.isdir(raw):
        for f in sorted(os.listdir(raw)):
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                photo_paths.append(os.path.join(raw, f))
    else:
        for p in raw.split(","):
            p = _clean_path(p)
            if os.path.isfile(p):
                photo_paths.append(p)
            else:
                print(f"  Uebersprungen (nicht gefunden): {p}")

    if not photo_paths:
        print("\nKeine Bilder gefunden.")
        return

    photo_paths = photo_paths[:10]
    print(f"\n{len(photo_paths)} Bild(er) gefunden. Verarbeitung startet...\n")

    season = get_season_context()
    _print_season_info(season)

    out = OutputManager()
    csv_rows = []

    for i, path in enumerate(photo_paths, 1):
        name = os.path.basename(path)
        print(f"\n--- [{i}/{len(photo_paths)}] {name} ---")

        try:
            print("  Foto wird analysiert...")
            product = analyze_photo(path)
            print(f"  Produkt: {product.get('product_name', '?')}")
            print(f"  Kategorie: {product.get('category', '?')}")

            print("  Etsy Listing wird erstellt...")
            listing = generate_listing(product, season)
            text = _format_listing_text(listing)
            etsy_path = out.save_etsy_listing(product.get("product_name", f"produkt-{i}"), text)
            print(f"    -> {etsy_path}")

            print("  Instagram Caption wird erstellt...")
            caption = generate_caption(product, season)
            cap_path = out.save_instagram_caption(product.get("product_name", f"produkt-{i}"), caption)
            print(f"    -> {cap_path}")

            csv_rows.append({
                "produkt": product.get("product_name", ""),
                "kategorie": product.get("category", ""),
                "titel": listing.get("title", ""),
                "tags": ", ".join(listing.get("tags", [])),
                "foto": path,
            })
        except Exception as e:
            print(f"  Fehler bei {name}: {e}")

    if csv_rows:
        csv_path = out.save_etsy_csv(csv_rows)
        print(f"\nCSV mit allen Listings: {csv_path}")

    print(f"\nAlle Dateien gespeichert in: {out.root}")
    print(f"Verarbeitet: {len(csv_rows)}/{len(photo_paths)} Produkte")


def main():
    print(HEADER)

    while True:
        print(MENU)
        choice = input("Deine Wahl (1-5): ").strip()

        try:
            if choice == "1":
                _single_product("both")
            elif choice == "2":
                _batch()
            elif choice == "3":
                _single_product("etsy")
            elif choice == "4":
                _single_product("instagram")
            elif choice == "5":
                print("\nServus! Bis zum naechsten Mal.\n")
                break
            else:
                print("\nBitte waehle 1-5.")
        except KeyboardInterrupt:
            print("\n\nServus! Bis zum naechsten Mal.\n")
            break
        except Exception as e:
            print(f"\nFehler: {e}")
            print("Bitte versuche es nochmal.\n")


if __name__ == "__main__":
    main()
