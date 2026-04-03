#!/usr/bin/env python3
"""Etsy-Produktbeschreibung Generator für Vo Herzn Handmade."""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()


def generiere_produktbeschreibung(produktname: str, stichworte: list) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden.")

    client = anthropic.Anthropic(api_key=api_key)

    stichworte_text = ", ".join(stichworte)

    prompt = f"""Du bist Texterin für einen kleinen bayerischen Handmade-Shop namens "Vo Herzn".
Der Shop verkauft liebevoll handgemachte Produkte – vor allem als Geschenke für Mütter und Kinder.

Erstelle für folgendes Produkt einen kompletten Etsy-Listing-Text auf Deutsch:

Produktname: {produktname}
Stichworte: {stichworte_text}

Schreibe:
1. TITEL: Einen ansprechenden Etsy-Titel (max. 140 Zeichen), der wichtige Keywords enthält
2. BESCHREIBUNG: Eine herzliche, persönliche Produktbeschreibung (ca. 150–200 Wörter).
   Der Ton soll warm, bayerisch-freundlich und einladend sein – wie von einer Freundin erzählt.
   Betone den Handmade-Charakter und die Eignung als Geschenk für Mütter oder Kinder.
3. TAGS: Genau 13 Etsy-Tags (je max. 20 Zeichen, kommagetrennt), die gut für die Suche geeignet sind.

Formatiere die Ausgabe exakt so:
TITEL:
[Titel hier]

BESCHREIBUNG:
[Beschreibung hier]

TAGS:
[tag1, tag2, tag3, ...]"""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        print("\n" + "─" * 50)
        result = ""
        for text in stream.text_stream:
            print(text, end="", flush=True)
            result += text
        print("\n" + "─" * 50)

    return result


def main():
    print("╔══════════════════════════════════════╗")
    print("║   Vo Herzn – Etsy Generator 🌸       ║")
    print("╚══════════════════════════════════════╝\n")

    produktname = input("Produktname: ").strip()
    if not produktname:
        print("Fehler: Bitte einen Produktnamen eingeben.")
        return

    print("Gib 3–4 Stichworte ein (mit Enter bestätigen, leere Eingabe = fertig):")
    stichworte = []
    while len(stichworte) < 4:
        stichwort = input(f"  Stichwort {len(stichworte) + 1}: ").strip()
        if not stichwort:
            if len(stichworte) < 3:
                print("Bitte mindestens 3 Stichworte eingeben.")
                continue
            break
        stichworte.append(stichwort)

    print(f"\nGeneriere Beschreibung für: {produktname}")
    print(f"Stichworte: {', '.join(stichworte)}")
    print("Bitte warten...\n")

    try:
        generiere_produktbeschreibung(produktname, stichworte)
    except ValueError as e:
        print(f"\nKonfigurationsfehler: {e}")
    except anthropic.AuthenticationError:
        print("\nFehler: Ungültiger API-Key. Bitte .env prüfen.")
    except anthropic.RateLimitError:
        print("\nFehler: API-Limit erreicht. Bitte kurz warten und erneut versuchen.")
    except anthropic.APIConnectionError:
        print("\nFehler: Keine Verbindung zur API. Internetverbindung prüfen.")
    except anthropic.APIStatusError as e:
        print(f"\nAPI-Fehler ({e.status_code}): {e.message}")


if __name__ == "__main__":
    main()
