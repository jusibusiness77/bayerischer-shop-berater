"""Etsy Listing Generator — erzeugt Titel, Beschreibung und Tags via Claude API."""

import os

import anthropic
from dotenv import load_dotenv


def _get_client() -> anthropic.Anthropic:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden")
    return anthropic.Anthropic(api_key=api_key)


def _parse_listing(text: str) -> dict:
    sections = {"title": "", "description": "", "tags": [], "raw": text}

    if "TITEL:" in text:
        after_titel = text.split("TITEL:", 1)[1]
        if "BESCHREIBUNG:" in after_titel:
            sections["title"] = after_titel.split("BESCHREIBUNG:", 1)[0].strip()[:140]
        else:
            sections["title"] = after_titel.strip().split("\n")[0].strip()[:140]

    if "BESCHREIBUNG:" in text:
        after_beschreibung = text.split("BESCHREIBUNG:", 1)[1]
        if "TAGS:" in after_beschreibung:
            sections["description"] = after_beschreibung.split("TAGS:", 1)[0].strip()
        else:
            sections["description"] = after_beschreibung.strip()

    if "TAGS:" in text:
        after_tags = text.split("TAGS:", 1)[1].strip()
        tags = [t.strip() for t in after_tags.split(",") if t.strip()]
        sections["tags"] = tags[:13]

    return sections


def generate_listing(product: dict, season: dict) -> dict:
    client = _get_client()

    prompt = f"""Du bist die Texterin fuer "Vo Herz'n", einen bayerischen Handmade-Shop auf Etsy.
Schreibe ein Etsy-Listing fuer folgendes Produkt:

PRODUKT:
- Name: {product.get('product_name', '')}
- Kategorie: {product.get('category', '')}
- Materialien: {', '.join(product.get('materials', []))}
- Farben: {', '.join(product.get('colors', []))}
- Besonderheiten: {', '.join(product.get('features', []))}

SAISONALER KONTEXT:
- Saison: {season.get('season', '')}
- Anlaesse: {', '.join(season.get('events', []))}
- Keywords: {', '.join(season.get('keywords', []))}
- Stimmung: {season.get('mood', '')}

Erstelle bitte:

TITEL:
(Max 140 Zeichen, SEO-optimiert, mit relevanten Keywords und Pipes als Trenner)

BESCHREIBUNG:
(150-200 Woerter, bayerisch-warm und herzlich, beschreibe das Produkt liebevoll, erwaehne Materialien und Anlass)

TAGS:
(Genau 13 Tags, jeweils max 20 Zeichen, kommagetrennt, SEO-relevant)

Antworte NUR mit TITEL:, BESCHREIBUNG: und TAGS: Abschnitten."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text
    return _parse_listing(response_text)
