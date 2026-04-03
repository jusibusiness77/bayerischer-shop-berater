# Vo Herz'n Content Creator — Design

## Zweck

Umfassendes Tool + Claude Code Skill fuer den Etsy-Shop "Vo Herz'n". Automatisiert Etsy-Listings, Instagram-Posts und Produktbeschreibungen basierend auf Produktfotos oder Textbeschreibungen. Bayerisch-warmer Ton, SEO-optimiert, saisonal angepasst.

## Projektstruktur

```
vo-herzn-projekt/
├── voherzn/                  # Python-Package
│   ├── __init__.py
│   ├── etsy.py               # Etsy Listing Generator
│   ├── instagram.py          # Instagram Caption + Bild-Generator
│   ├── vision.py             # Produktfotos analysieren (Claude Vision)
│   ├── season.py             # Saisonale Erkennung + Anpassung
│   └── output.py             # Output auf Desktop verwalten
├── cli.py                    # CLI-Tool fuer Mama
├── website/
│   └── index.html            # Landing Page
├── skills/
│   └── vo-herzn.md           # Claude Code Skill
├── requirements.txt
├── .env
└── CLAUDE.md
```

Alte Einzelscripts (etsy_generator.py, instagram_post.py, create_logo.py, hallo.py) werden durch die neuen Module ersetzt und geloescht.

## Module

### vision.py — Foto-Analyse
- Nimmt 1-10 Produktfotos entgegen
- Schickt Fotos als Base64 an Claude Vision API (claude-sonnet-4-6)
- Gibt zurueck: Produktname, Kategorie, Materialien, Farben, besondere Merkmale
- Basis fuer alle anderen Module

### season.py — Saisonale Anpassung
- Datumsbasierte Erkennung (kein externes API)
- Zeitfenster: Fruehling/Ostern/Muttertag, Sommer, Herbst/Erntedank/Halloween, Winter/Advent/Weihnachten/Silvester
- Gibt passende Keywords, Stimmungswoerter und Hashtags zurueck

### etsy.py — Listing Generator
- Input: Vision-Analyse + saisonale Daten
- Claude API (claude-opus-4-6) generiert:
  - Titel (max. 140 Zeichen, SEO-optimiert, deutsch)
  - Beschreibung (150-200 Woerter, bayerisch-warm, Handmade betont)
  - 13 Tags (je max. 20 Zeichen, Etsy-konform)
- Output: .txt pro Produkt + .csv fuer Bulk-Upload

### instagram.py — Instagram Generator
- Input: Vision-Analyse + saisonale Daten
- Erstellt:
  - Caption im Vo Herzn Stil (bayerisch, authentisch)
  - 30 Hashtags (Mix aus grossen und Nischen-Hashtags)
  - Post-Bild (1080x1080px, Vo Herzn Branding)

### output.py — Output Manager
- Erstellt pro Durchlauf einen Ordner auf dem Desktop:
```
~/Desktop/Vo Herzn Output/2026-04-03/
├── etsy/
│   ├── produkt-1-listing.txt
│   └── alle-listings.csv
├── instagram/
│   ├── produkt-1-caption.txt
│   └── produkt-1-post.png
└── zusammenfassung.txt
```

## CLI Tool (cli.py)

Einfaches Terminal-Menu mit 4 Optionen:
1. Einzelnes Produkt (Foto oder Beschreibung)
2. Mehrere Produkte (bis zu 10 Fotos, Batch)
3. Nur Etsy Listing
4. Nur Instagram Post

Ablauf: Foto/Text eingeben -> Vision analysiert -> Saison wird angewendet -> Content generiert -> Output auf Desktop

## Claude Code Skill (vo-herzn.md)

- Trigger: Etsy-Listings, Instagram-Posts, Produktbeschreibungen, Vo Herzn Content
- Interaktiver Workflow: Fotos entgegennehmen, Module aufrufen, Ergebnisse reviewen und iterieren
- Saisonale Vorschlaege automatisch
- Kann einzelne Module oder alles zusammen aufrufen

## Technische Details

- **Vision:** claude-sonnet-4-6 (schneller/guenstiger fuer Bildanalyse)
- **Textgenerierung:** claude-opus-4-6 (beste Qualitaet fuer Texte)
- **Dependencies:** anthropic, python-dotenv, Pillow, pilmoji (alle bereits vorhanden)
- **Saisonale Erkennung:** Rein datumsbasiert, feste Zeitfenster, erweiterbar

## Spaeter erweiterbar

- Etsy API Integration (Listings direkt als Entwurf hochladen)
- Instagram API (direkt posten)
- Etsy Analytics (Tag-Performance)
