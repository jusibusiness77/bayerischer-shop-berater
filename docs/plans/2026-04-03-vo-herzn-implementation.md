# Vo Herz'n Content Creator — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a modular Python tool + Claude Code Skill that generates Etsy listings and Instagram posts from product photos, with seasonal adjustments and batch processing.

**Architecture:** Python package `voherzn/` with 5 modules (vision, season, etsy, instagram, output), a CLI entry point, and a Claude Code skill file. Vision analyzes photos via Claude API, season adds context, etsy/instagram generate content, output manages Desktop file structure.

**Tech Stack:** Python 3, anthropic SDK (Vision + Text), Pillow + pilmoji (image generation), python-dotenv

---

### Task 1: Project scaffolding

**Files:**
- Create: `voherzn/__init__.py`
- Create: `tests/__init__.py`
- Modify: `requirements.txt`

**Step 1: Create package directory and init**

```bash
mkdir -p voherzn tests
```

```python
# voherzn/__init__.py
"""Vo Herz'n Content Creator — Automatisierung fuer den Etsy-Shop."""
```

```python
# tests/__init__.py
```

**Step 2: Update requirements.txt**

```
anthropic>=0.40.0
python-dotenv>=1.0.0
Pillow>=10.0.0
pilmoji>=2.0.0
pytest>=8.0.0
```

**Step 3: Install dependencies**

Run: `pip install -r requirements.txt`

**Step 4: Commit**

```bash
git init  # falls noch kein Repo
git add voherzn/__init__.py tests/__init__.py requirements.txt
git commit -m "chore: scaffold voherzn package structure"
```

---

### Task 2: season.py — Saisonale Erkennung

**Files:**
- Create: `voherzn/season.py`
- Create: `tests/test_season.py`

**Step 1: Write failing tests**

```python
# tests/test_season.py
from datetime import date
from voherzn.season import get_season_context


def test_muttertag_3_weeks_before():
    # Muttertag 2026 = 10. Mai, 3 Wochen vorher = 19. April
    ctx = get_season_context(date(2026, 4, 20))
    assert "Muttertag" in ctx["events"]
    assert any("Muttertag" in kw or "Mama" in kw for kw in ctx["keywords"])


def test_weihnachten_advent():
    ctx = get_season_context(date(2026, 12, 5))
    assert "Weihnachten" in ctx["events"]
    assert ctx["season"] == "Winter"


def test_ostern():
    # Ostern 2026 = 5. April, 3 Wochen vorher = 15. Maerz
    ctx = get_season_context(date(2026, 3, 20))
    assert "Ostern" in ctx["events"]


def test_sommer_keine_feiertage():
    ctx = get_season_context(date(2026, 7, 15))
    assert ctx["season"] == "Sommer"
    assert len(ctx["events"]) == 0


def test_context_has_required_keys():
    ctx = get_season_context(date(2026, 6, 1))
    assert "season" in ctx
    assert "events" in ctx
    assert "keywords" in ctx
    assert "hashtags" in ctx
    assert "mood" in ctx
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_season.py -v`
Expected: FAIL with "cannot import name 'get_season_context'"

**Step 3: Implement season.py**

```python
# voherzn/season.py
"""Saisonale Erkennung und Anpassung fuer Vo Herz'n Texte."""

from datetime import date


# Ostern-Berechnung (Gauss-Algorithmus)
def _easter(year: int) -> date:
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


# Muttertag = 2. Sonntag im Mai
def _muttertag(year: int) -> date:
    may1 = date(year, 5, 1)
    # Tage bis zum ersten Sonntag
    days_to_sunday = (6 - may1.weekday()) % 7
    first_sunday = may1.day + days_to_sunday
    second_sunday = first_sunday + 7
    return date(year, 5, second_sunday)


SEASON_RANGES = {
    "Fruehling": ((3, 1), (5, 31)),
    "Sommer": ((6, 1), (8, 31)),
    "Herbst": ((9, 1), (11, 30)),
    "Winter": ((12, 1), (2, 28)),
}

SEASON_MOODS = {
    "Fruehling": "frisch, farbenfroh, Aufbruchstimmung",
    "Sommer": "leicht, sonnig, lebensfroh",
    "Herbst": "gemuetlich, warm, erdige Toene",
    "Winter": "besinnlich, festlich, kuschelig",
}

SEASON_KEYWORDS = {
    "Fruehling": ["Fruehlingsdeko", "frische Farben", "Fruehlingsgefuehle"],
    "Sommer": ["Sommerdeko", "Garten", "leichte Accessoires"],
    "Herbst": ["Herbstdeko", "Kuerbis", "warme Farben", "gemuetlich"],
    "Winter": ["Winterdeko", "kuschelig", "Winterzauber"],
}

SEASON_HASHTAGS = {
    "Fruehling": ["#fruehlingsdeko", "#springvibes", "#fruehlingsliebe"],
    "Sommer": ["#sommerdeko", "#summervibes", "#sommerliebe"],
    "Herbst": ["#herbstdeko", "#autumnvibes", "#herbstliebe", "#cozyautumn"],
    "Winter": ["#winterdeko", "#wintervibes", "#winterzauber"],
}


def _get_season(d: date) -> str:
    month = d.month
    if 3 <= month <= 5:
        return "Fruehling"
    elif 6 <= month <= 8:
        return "Sommer"
    elif 9 <= month <= 11:
        return "Herbst"
    else:
        return "Winter"


def _get_events(d: date) -> list[dict]:
    events = []
    year = d.year

    # Ostern (3 Wochen vorher bis zum Tag)
    easter = _easter(year)
    easter_start = date(year, easter.month, easter.day - 21) if easter.day > 21 else date(year, easter.month - 1, easter.day + 7)
    from datetime import timedelta
    easter_start = easter - timedelta(days=21)
    if easter_start <= d <= easter:
        events.append({
            "name": "Ostern",
            "keywords": ["Ostergeschenk", "Osterdeko", "Fruehling", "Osternest"],
            "hashtags": ["#ostern", "#osterdeko", "#ostergeschenk", "#osterhase"],
        })

    # Muttertag (3 Wochen vorher bis zum Tag)
    mt = _muttertag(year)
    mt_start = mt - timedelta(days=21)
    if mt_start <= d <= mt:
        events.append({
            "name": "Muttertag",
            "keywords": ["Muttertagsgeschenk", "Geschenk fuer Mama", "Mama", "Danke Mama"],
            "hashtags": ["#muttertag", "#muttertagsgeschenk", "#besteMama", "#fuermama"],
        })

    # Halloween (ab 1. Oktober)
    if date(year, 10, 1) <= d <= date(year, 10, 31):
        events.append({
            "name": "Halloween",
            "keywords": ["Herbstdeko", "Halloween", "Kuerbis", "gruselig-schoen"],
            "hashtags": ["#halloween", "#halloweendeko", "#herbst"],
        })

    # Advent/Weihnachten (ab 20. November)
    if d >= date(year, 11, 20) or d <= date(year, 1, 6):
        check_year = year if d.month >= 11 else year - 1
        events.append({
            "name": "Weihnachten",
            "keywords": ["Weihnachtsgeschenk", "Adventsdeko", "Christkind", "Bescherung", "handgemachtes Geschenk"],
            "hashtags": ["#weihnachten", "#advent", "#weihnachtsgeschenk", "#christkind", "#xmas"],
        })

    # Valentinstag (2 Wochen vorher bis zum Tag)
    valentinstag = date(year, 2, 14)
    if valentinstag - timedelta(days=14) <= d <= valentinstag:
        events.append({
            "name": "Valentinstag",
            "keywords": ["Valentinstagsgeschenk", "Geschenk mit Herz", "Liebe"],
            "hashtags": ["#valentinstag", "#valentinesday", "#geschenkidee"],
        })

    return events


def get_season_context(d: date | None = None) -> dict:
    """Gibt den saisonalen Kontext fuer ein Datum zurueck."""
    if d is None:
        d = date.today()

    season = _get_season(d)
    events = _get_events(d)

    event_names = [e["name"] for e in events]
    extra_keywords = []
    extra_hashtags = []
    for e in events:
        extra_keywords.extend(e["keywords"])
        extra_hashtags.extend(e["hashtags"])

    return {
        "season": season,
        "events": event_names,
        "keywords": SEASON_KEYWORDS.get(season, []) + extra_keywords,
        "hashtags": SEASON_HASHTAGS.get(season, []) + extra_hashtags,
        "mood": SEASON_MOODS.get(season, ""),
    }
```

**Step 4: Run tests**

Run: `pytest tests/test_season.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add voherzn/season.py tests/test_season.py
git commit -m "feat: add seasonal detection module"
```

---

### Task 3: output.py — Output Manager

**Files:**
- Create: `voherzn/output.py`
- Create: `tests/test_output.py`

**Step 1: Write failing tests**

```python
# tests/test_output.py
import os
import shutil
from datetime import date
from voherzn.output import OutputManager


def test_creates_desktop_directory(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    assert os.path.isdir(om.root)
    assert "2026-04-03" in om.root


def test_creates_subdirectories(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    assert os.path.isdir(om.etsy_dir)
    assert os.path.isdir(om.instagram_dir)


def test_save_etsy_listing(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    path = om.save_etsy_listing("Filztasche", "TITEL:\nTest\n\nBESCHREIBUNG:\nTest\n\nTAGS:\na,b,c")
    assert os.path.isfile(path)
    assert "filztasche" in path.lower()


def test_save_instagram_caption(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    path = om.save_instagram_caption("Filztasche", "Tolle Caption #voherzn")
    assert os.path.isfile(path)


def test_save_summary(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    path = om.save_summary(["Filztasche: Etsy + Instagram erstellt"])
    assert os.path.isfile(path)
    assert "zusammenfassung" in path.lower()


def test_duplicate_date_gets_counter(tmp_path):
    om1 = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    om2 = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    assert om1.root != om2.root
    assert "_1" in om2.root or "_2" in om2.root
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_output.py -v`
Expected: FAIL

**Step 3: Implement output.py**

```python
# voherzn/output.py
"""Output Manager — speichert generierte Inhalte auf den Desktop."""

import os
import re
from datetime import date


DEFAULT_BASE = os.path.expanduser("~/Desktop/Vo Herzn Output")


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9äöüß]+", "-", text)
    return text.strip("-")


class OutputManager:
    def __init__(self, base_dir: str = DEFAULT_BASE, d: date | None = None):
        if d is None:
            d = date.today()
        self.date_str = d.strftime("%Y-%m-%d")

        self.root = os.path.join(base_dir, self.date_str)
        counter = 1
        while os.path.exists(self.root):
            self.root = os.path.join(base_dir, f"{self.date_str}_{counter}")
            counter += 1

        self.etsy_dir = os.path.join(self.root, "etsy")
        self.instagram_dir = os.path.join(self.root, "instagram")
        os.makedirs(self.etsy_dir, exist_ok=True)
        os.makedirs(self.instagram_dir, exist_ok=True)

    def save_etsy_listing(self, product_name: str, content: str) -> str:
        slug = _slugify(product_name)
        path = os.path.join(self.etsy_dir, f"{slug}-listing.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def save_etsy_csv(self, rows: list[dict]) -> str:
        import csv
        path = os.path.join(self.etsy_dir, "alle-listings.csv")
        if not rows:
            return path
        fieldnames = rows[0].keys()
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def save_instagram_caption(self, product_name: str, caption: str) -> str:
        slug = _slugify(product_name)
        path = os.path.join(self.instagram_dir, f"{slug}-caption.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(caption)
        return path

    def save_instagram_image(self, product_name: str, image) -> str:
        slug = _slugify(product_name)
        path = os.path.join(self.instagram_dir, f"{slug}-post.png")
        image.save(path, "PNG")
        return path

    def save_summary(self, entries: list[str]) -> str:
        path = os.path.join(self.root, "zusammenfassung.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("Vo Herz'n — Zusammenfassung\n")
            f.write(f"Datum: {self.date_str}\n")
            f.write("=" * 40 + "\n\n")
            for entry in entries:
                f.write(f"- {entry}\n")
        return path
```

**Step 4: Run tests**

Run: `pytest tests/test_output.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add voherzn/output.py tests/test_output.py
git commit -m "feat: add output manager for Desktop file structure"
```

---

### Task 4: vision.py — Foto-Analyse

**Files:**
- Create: `voherzn/vision.py`
- Create: `tests/test_vision.py`

**Step 1: Write failing tests**

```python
# tests/test_vision.py
import json
from unittest.mock import patch, MagicMock
from voherzn.vision import analyze_photo, analyze_photos


MOCK_VISION_RESPONSE = {
    "product_name": "Filztasche altrosa",
    "category": "Tasche",
    "materials": ["Filz", "Baumwolle"],
    "colors": ["altrosa", "creme"],
    "features": ["handgenaeht", "Tiermotiv", "Innentasche"],
}


def _mock_client():
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(MOCK_VISION_RESPONSE))]
    mock.messages.create.return_value = mock_message
    return mock


def test_analyze_photo_returns_required_keys():
    with patch("voherzn.vision._get_client", return_value=_mock_client()):
        result = analyze_photo("tests/fixtures/test.jpg")
    assert "product_name" in result
    assert "category" in result
    assert "materials" in result
    assert "colors" in result
    assert "features" in result


def test_analyze_photo_parses_json():
    with patch("voherzn.vision._get_client", return_value=_mock_client()):
        result = analyze_photo("tests/fixtures/test.jpg")
    assert result["product_name"] == "Filztasche altrosa"
    assert "Filz" in result["materials"]


def test_analyze_photos_batch():
    with patch("voherzn.vision._get_client", return_value=_mock_client()):
        results = analyze_photos(["img1.jpg", "img2.jpg", "img3.jpg"])
    assert len(results) == 3


def test_analyze_photos_max_10():
    with patch("voherzn.vision._get_client", return_value=_mock_client()):
        paths = [f"img{i}.jpg" for i in range(15)]
        results = analyze_photos(paths)
    assert len(results) == 10
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_vision.py -v`
Expected: FAIL

**Step 3: Create test fixture**

```bash
mkdir -p tests/fixtures
# 1x1 pixel JPEG fuer Tests
python3 -c "from PIL import Image; Image.new('RGB',(1,1)).save('tests/fixtures/test.jpg')"
```

**Step 4: Implement vision.py**

```python
# voherzn/vision.py
"""Produktfoto-Analyse per Claude Vision API."""

import os
import json
import base64
import mimetypes
import anthropic
from dotenv import load_dotenv

load_dotenv()

MAX_PHOTOS = 10


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden.")
    return anthropic.Anthropic(api_key=api_key)


def _encode_image(path: str) -> tuple[str, str]:
    mime_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, mime_type


VISION_PROMPT = """Analysiere dieses Produktfoto fuer einen handgemachten bayerischen Shop namens "Vo Herz'n".
Der Shop verkauft Deko, Accessoires, Taschen und Unikate.

Antworte NUR mit einem JSON-Objekt in diesem Format:
{
    "product_name": "Name des Produkts",
    "category": "Deko | Tasche | Accessoire | Gravur | Unikat",
    "materials": ["Material 1", "Material 2"],
    "colors": ["Farbe 1", "Farbe 2"],
    "features": ["Merkmal 1", "Merkmal 2", "Merkmal 3"]
}

Kein zusaetzlicher Text, nur das JSON."""


def analyze_photo(photo_path: str) -> dict:
    """Analysiert ein einzelnes Produktfoto und gibt strukturierte Daten zurueck."""
    client = _get_client()
    image_data, mime_type = _encode_image(photo_path)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data,
                    },
                },
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )

    response_text = message.content[0].text.strip()
    # JSON aus Antwort extrahieren (falls in Markdown-Block)
    if "```" in response_text:
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    return json.loads(response_text)


def analyze_photos(photo_paths: list[str]) -> list[dict]:
    """Analysiert mehrere Fotos (max 10)."""
    paths = photo_paths[:MAX_PHOTOS]
    results = []
    for path in paths:
        result = analyze_photo(path)
        result["source_photo"] = path
        results.append(result)
    return results


def analyze_from_text(description: str) -> dict:
    """Erstellt Produktdaten aus einer Textbeschreibung (ohne Foto)."""
    client = _get_client()

    prompt = f"""Erstelle aus dieser Produktbeschreibung strukturierte Daten fuer den Shop "Vo Herz'n".

Beschreibung: {description}

Antworte NUR mit JSON:
{{
    "product_name": "Name",
    "category": "Deko | Tasche | Accessoire | Gravur | Unikat",
    "materials": ["Material 1"],
    "colors": ["Farbe 1"],
    "features": ["Merkmal 1"]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    if "```" in response_text:
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    return json.loads(response_text)
```

**Step 5: Run tests**

Run: `pytest tests/test_vision.py -v`
Expected: All 4 tests PASS

**Step 6: Commit**

```bash
git add voherzn/vision.py tests/test_vision.py tests/fixtures/test.jpg
git commit -m "feat: add vision module for product photo analysis"
```

---

### Task 5: etsy.py — Listing Generator

**Files:**
- Create: `voherzn/etsy.py`
- Create: `tests/test_etsy.py`

**Step 1: Write failing tests**

```python
# tests/test_etsy.py
from unittest.mock import patch, MagicMock
from voherzn.etsy import generate_listing


MOCK_PRODUCT = {
    "product_name": "Filztasche altrosa",
    "category": "Tasche",
    "materials": ["Filz", "Baumwolle"],
    "colors": ["altrosa", "creme"],
    "features": ["handgenaeht", "Tiermotiv"],
}

MOCK_SEASON = {
    "season": "Fruehling",
    "events": ["Muttertag"],
    "keywords": ["Muttertagsgeschenk"],
    "hashtags": [],
    "mood": "frisch, farbenfroh",
}

MOCK_LISTING_TEXT = """TITEL:
Filztasche altrosa handgemacht | Geschenk Muttertag | Handtasche Bayern

BESCHREIBUNG:
Eine wunderschoene Filztasche in zartem Altrosa, mit viel Liebe handgenaeht.

TAGS:
Filztasche, altrosa, handgemacht, Muttertag, Bayern, Geschenk, Handtasche, Unikat, Deko, handgenaeht, Tasche, Filz, Liebe"""


def _mock_client():
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=MOCK_LISTING_TEXT)]
    mock.messages.create.return_value = mock_message
    return mock


def test_generate_listing_returns_required_sections():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert "title" in result
    assert "description" in result
    assert "tags" in result


def test_generate_listing_has_13_tags():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert len(result["tags"]) == 13


def test_generate_listing_title_max_140():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert len(result["title"]) <= 140


def test_generate_listing_raw_text():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert "raw" in result
    assert "TITEL:" in result["raw"]
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_etsy.py -v`
Expected: FAIL

**Step 3: Implement etsy.py**

```python
# voherzn/etsy.py
"""Etsy Listing Generator fuer Vo Herz'n."""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden.")
    return anthropic.Anthropic(api_key=api_key)


def _build_prompt(product: dict, season: dict) -> str:
    season_hint = ""
    if season["events"]:
        season_hint = f"\nAktuelle Anlaesse: {', '.join(season['events'])}. Baue diese Anlaesse subtil in den Text ein."
    if season["keywords"]:
        season_hint += f"\nSaisonale Keywords die du einbauen kannst: {', '.join(season['keywords'][:5])}"
    season_hint += f"\nStimmung der Saison: {season['mood']}"

    return f"""Du bist Texterin fuer einen kleinen bayerischen Handmade-Shop namens "Vo Herz'n".
Der Shop verkauft liebevoll handgemachte Produkte — Deko, Accessoires, Taschen und Unikate.

Erstelle ein komplettes Etsy-Listing auf Deutsch:

Produkt: {product['product_name']}
Kategorie: {product['category']}
Materialien: {', '.join(product['materials'])}
Farben: {', '.join(product['colors'])}
Merkmale: {', '.join(product['features'])}
Saison: {season['season']}
{season_hint}

Schreibe:
1. TITEL: Ansprechender Etsy-Titel (max. 140 Zeichen), SEO-optimiert mit wichtigen Keywords
2. BESCHREIBUNG: Herzliche Produktbeschreibung (150-200 Woerter). Ton: bayerisch-warm, persoenlich, wie von einer Freundin erzaehlt. Betone Handmade-Charakter.
3. TAGS: Genau 13 Etsy-Tags (je max. 20 Zeichen, kommagetrennt), SEO-optimiert fuer den deutschsprachigen Raum.

Formatiere exakt so:
TITEL:
[Titel]

BESCHREIBUNG:
[Beschreibung]

TAGS:
[tag1, tag2, tag3, ...]"""


def _parse_listing(text: str) -> dict:
    sections = {}
    current = None
    lines = text.strip().split("\n")

    for line in lines:
        stripped = line.strip()
        if stripped == "TITEL:":
            current = "title"
            sections[current] = []
        elif stripped == "BESCHREIBUNG:":
            current = "description"
            sections[current] = []
        elif stripped == "TAGS:":
            current = "tags"
            sections[current] = []
        elif current:
            sections[current].append(line)

    title = "\n".join(sections.get("title", [])).strip()
    description = "\n".join(sections.get("description", [])).strip()
    tags_raw = "\n".join(sections.get("tags", [])).strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    return {
        "title": title[:140],
        "description": description,
        "tags": tags[:13],
        "raw": text,
    }


def generate_listing(product: dict, season: dict) -> dict:
    """Generiert ein Etsy-Listing fuer ein Produkt."""
    client = _get_client()
    prompt = _build_prompt(product, season)

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()
    return _parse_listing(raw_text)
```

**Step 4: Run tests**

Run: `pytest tests/test_etsy.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add voherzn/etsy.py tests/test_etsy.py
git commit -m "feat: add Etsy listing generator module"
```

---

### Task 6: instagram.py — Instagram Generator

**Files:**
- Create: `voherzn/instagram.py`
- Create: `tests/test_instagram.py`

**Step 1: Write failing tests**

```python
# tests/test_instagram.py
import os
from unittest.mock import patch, MagicMock
from voherzn.instagram import generate_caption, create_post_image


MOCK_PRODUCT = {
    "product_name": "Filztasche altrosa",
    "category": "Tasche",
    "materials": ["Filz"],
    "colors": ["altrosa"],
    "features": ["handgenaeht"],
}

MOCK_SEASON = {
    "season": "Fruehling",
    "events": ["Muttertag"],
    "keywords": ["Muttertagsgeschenk"],
    "hashtags": ["#muttertag", "#fruehlingsdeko"],
    "mood": "frisch, farbenfroh",
}

MOCK_CAPTION = """Vo Herz'n — mit Liebe handgemacht!

Unsere neue Filztasche in zartem Altrosa ist da!

#voherzn #handgemacht #muttertag #bayern #filztasche"""


def _mock_client():
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=MOCK_CAPTION)]
    mock.messages.create.return_value = mock_message
    return mock


def test_generate_caption_returns_text():
    with patch("voherzn.instagram._get_client", return_value=_mock_client()):
        caption = generate_caption(MOCK_PRODUCT, MOCK_SEASON)
    assert isinstance(caption, str)
    assert len(caption) > 0


def test_generate_caption_has_hashtags():
    with patch("voherzn.instagram._get_client", return_value=_mock_client()):
        caption = generate_caption(MOCK_PRODUCT, MOCK_SEASON)
    assert "#" in caption


def test_create_post_image_returns_pil_image():
    img = create_post_image("Neue Filztasche — vo Herz'n")
    assert img.size == (1080, 1080)


def test_create_post_image_saveable(tmp_path):
    img = create_post_image("Test")
    path = os.path.join(str(tmp_path), "test.png")
    img.save(path, "PNG")
    assert os.path.isfile(path)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_instagram.py -v`
Expected: FAIL

**Step 3: Implement instagram.py**

Port the existing `instagram_post.py` image generation into the module and add caption generation:

```python
# voherzn/instagram.py
"""Instagram Caption + Bild Generator fuer Vo Herz'n."""

import os
import math
import anthropic
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource
from dotenv import load_dotenv

load_dotenv()

BG_COLOR = "#FAF0F2"
ALTROSA = "#C17A8A"
DUNKELROT = "#5C2D3A"
FONT_DIR = os.path.expanduser("~/.voherzn_fonts")
SIZE = 1080


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden.")
    return anthropic.Anthropic(api_key=api_key)


def _load_font(filename, size):
    path = os.path.join(FONT_DIR, filename)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _draw_heart(draw, cx, cy, size, color):
    points = []
    for i in range(201):
        t = 2 * math.pi * i / 200
        x = size * 16 * math.sin(t) ** 3
        y = -size * (13 * math.cos(t) - 5 * math.cos(2 * t)
                     - 2 * math.cos(3 * t) - math.cos(4 * t))
        points.append((cx + x, cy + y))
    draw.polygon(points, fill=color)


def _wrap_text(pilmoji, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        w, _ = pilmoji.getsize(test, font=font)
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_caption(product: dict, season: dict) -> str:
    """Generiert eine Instagram-Caption mit Hashtags."""
    client = _get_client()

    season_hint = ""
    if season["events"]:
        season_hint = f"\nAktuelle Anlaesse: {', '.join(season['events'])}"
    hashtag_suggestions = season["hashtags"][:5] if season["hashtags"] else []

    prompt = f"""Du schreibst Instagram-Captions fuer "Vo Herz'n", einen kleinen bayerischen Handmade-Shop.

Produkt: {product['product_name']}
Kategorie: {product['category']}
Materialien: {', '.join(product['materials'])}
Merkmale: {', '.join(product['features'])}
Saison: {season['season']}
{season_hint}

Schreibe eine Instagram-Caption:
- Ton: bayerisch-warm, authentisch, persoenlich, mit Herz
- Laenge: 3-5 kurze Absaetze
- Am Ende: genau 30 Hashtags (Mix aus grossen und Nischen-Hashtags)
- Immer dabei: #voherzn #handgemacht #bayern #handmade
- Saisonale Hashtags einbauen: {', '.join(hashtag_suggestions)}

Schreibe NUR die Caption, keinen zusaetzlichen Text."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()


def create_post_image(post_text: str) -> Image.Image:
    """Erstellt ein Instagram-Post-Bild (1080x1080) im Vo Herz'n Design."""
    img = Image.new("RGB", (SIZE, SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_brand = _load_font("GreatVibes-Regular.ttf", 72)
    font_post = _load_font("Lato-Light.ttf", 52)
    font_footer1 = _load_font("Lato-Regular.ttf", 26)
    font_footer2 = _load_font("Lato-Light.ttf", 20)

    # Rahmen
    m = 32
    draw.rectangle([m, m, SIZE - m, SIZE - m], outline=ALTROSA, width=1)
    draw.rectangle([m + 8, m + 8, SIZE - m - 8, SIZE - m - 8], outline=ALTROSA, width=1)

    # Branding
    brand_text = "Vo Herz\u00b4n"
    bw = draw.textlength(brand_text, font=font_brand)
    draw.text(((SIZE - bw) / 2, 58), brand_text, font=font_brand, fill=DUNKELROT)
    _draw_heart(draw, SIZE // 2 - int(bw) // 2 - 38, 97, 1.6, ALTROSA)

    # Zierlinie
    line_w = 400
    lx = (SIZE - line_w) // 2
    ly = 155
    mid = SIZE // 2
    draw.line([(lx, ly), (lx + line_w, ly)], fill=ALTROSA, width=1)
    draw.polygon([(mid, ly - 5), (mid + 5, ly), (mid, ly + 5), (mid - 5, ly)], fill=ALTROSA)

    # Post-Text
    max_w = SIZE - 160
    text_area_top = ly + 40
    text_area_bot = SIZE - 200

    with Pilmoji(img, source=GoogleEmojiSource) as pilmoji:
        lines = _wrap_text(pilmoji, post_text, font_post, max_w)
        sample_bbox = draw.textbbox((0, 0), "Ag", font=font_post)
        line_h = (sample_bbox[3] - sample_bbox[1]) + 18
        total_h = len(lines) * line_h
        start_y = text_area_top + ((text_area_bot - text_area_top) - total_h) // 2

        for i, line in enumerate(lines):
            lw, _ = pilmoji.getsize(line, font=font_post)
            pilmoji.text(
                ((SIZE - lw) // 2, start_y + i * line_h),
                line, font=font_post, fill=DUNKELROT, emoji_scale_factor=1.1,
            )

    _draw_heart(draw, 90, text_area_top + 30, 2.0, ALTROSA)

    # Footer
    fly = SIZE - 175
    draw.line([(lx, fly), (lx + line_w, fly)], fill=ALTROSA, width=1)
    draw.polygon([(mid, fly - 5), (mid + 5, fly), (mid, fly + 5), (mid - 5, fly)], fill=ALTROSA)

    fw1 = draw.textlength("hand\u00b4gmacht mit Liebe", font=font_footer1)
    draw.text(((SIZE - fw1) / 2, fly + 18), "hand\u00b4gmacht mit Liebe",
              font=font_footer1, fill=ALTROSA)

    foot2 = "DEKO  \u00b7  GRAVUR  \u00b7  UNIKATE  \u00b7  BAYERN"
    fw2 = draw.textlength(foot2, font=font_footer2)
    draw.text(((SIZE - fw2) / 2, fly + 56), foot2, font=font_footer2, fill=DUNKELROT)

    return img
```

**Step 4: Run tests**

Run: `pytest tests/test_instagram.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add voherzn/instagram.py tests/test_instagram.py
git commit -m "feat: add Instagram caption and image generator"
```

---

### Task 7: cli.py — CLI Tool fuer Mama

**Files:**
- Create: `cli.py`

**Step 1: Implement cli.py**

```python
#!/usr/bin/env python3
"""Vo Herz'n Content Creator — CLI Tool."""

import os
import sys
from voherzn.vision import analyze_photo, analyze_photos, analyze_from_text
from voherzn.season import get_season_context
from voherzn.etsy import generate_listing
from voherzn.instagram import generate_caption, create_post_image
from voherzn.output import OutputManager


def print_header():
    print("\n" + "=" * 44)
    print("   Vo Herz'n — Content Creator")
    print("=" * 44)


def print_menu():
    print("\nWas moechtest du machen?\n")
    print("  1. Einzelnes Produkt  (Foto oder Beschreibung)")
    print("  2. Mehrere Produkte   (bis zu 10 Fotos)")
    print("  3. Nur Etsy Listing")
    print("  4. Nur Instagram Post")
    print("  5. Beenden")
    print()


def get_product_input() -> dict:
    print("\nHast du ein Foto oder eine Beschreibung?")
    print("  1. Foto (Pfad eingeben oder reinziehen)")
    print("  2. Textbeschreibung")
    choice = input("\nDeine Wahl: ").strip()

    if choice == "1":
        path = input("Foto-Pfad: ").strip().strip("'\"")
        if not os.path.isfile(path):
            print(f"Datei nicht gefunden: {path}")
            return None
        print("Analysiere Foto...")
        return analyze_photo(path)
    elif choice == "2":
        desc = input("Kurze Beschreibung: ").strip()
        if not desc:
            print("Keine Beschreibung eingegeben.")
            return None
        print("Analysiere Beschreibung...")
        return analyze_from_text(desc)
    else:
        print("Ungueltige Eingabe.")
        return None


def process_single(mode: str = "both"):
    """Verarbeitet ein einzelnes Produkt. mode: 'both', 'etsy', 'instagram'"""
    product = get_product_input()
    if not product:
        return

    season = get_season_context()
    output = OutputManager()

    print(f"\nProdukt: {product['product_name']}")
    print(f"Kategorie: {product['category']}")
    print(f"Saison: {season['season']}", end="")
    if season["events"]:
        print(f" ({', '.join(season['events'])})")
    else:
        print()

    summary = []

    if mode in ("both", "etsy"):
        print("\nGeneriere Etsy-Listing...")
        listing = generate_listing(product, season)
        path = output.save_etsy_listing(product["product_name"], listing["raw"])
        print(f"  Titel: {listing['title']}")
        print(f"  Tags: {', '.join(listing['tags'][:5])}...")
        print(f"  Gespeichert: {path}")
        summary.append(f"{product['product_name']}: Etsy-Listing erstellt")

    if mode in ("both", "instagram"):
        print("\nGeneriere Instagram-Post...")
        caption = generate_caption(product, season)
        caption_path = output.save_instagram_caption(product["product_name"], caption)

        short_text = product["product_name"] + " — vo Herz'n"
        img = create_post_image(short_text)
        img_path = output.save_instagram_image(product["product_name"], img)

        print(f"  Caption gespeichert: {caption_path}")
        print(f"  Bild gespeichert: {img_path}")
        summary.append(f"{product['product_name']}: Instagram-Post erstellt")

    output.save_summary(summary)
    print(f"\nAlles gespeichert in: {output.root}")


def process_batch():
    print("\nGib den Ordner mit Fotos ein (oder einzelne Pfade, leere Zeile = fertig):")
    first = input("Ordner oder Foto-Pfad: ").strip().strip("'\"")

    paths = []
    if os.path.isdir(first):
        for f in sorted(os.listdir(first)):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                paths.append(os.path.join(first, f))
        print(f"  {len(paths)} Fotos gefunden.")
    else:
        if os.path.isfile(first):
            paths.append(first)
        while len(paths) < 10:
            p = input(f"  Foto {len(paths) + 1} (leer = fertig): ").strip().strip("'\"")
            if not p:
                break
            if os.path.isfile(p):
                paths.append(p)
            else:
                print(f"    Nicht gefunden: {p}")

    if not paths:
        print("Keine Fotos gefunden.")
        return

    print(f"\nVerarbeite {len(paths)} Fotos...")
    season = get_season_context()
    output = OutputManager()
    summary = []
    csv_rows = []

    for i, path in enumerate(paths[:10]):
        print(f"\n[{i + 1}/{len(paths)}] {os.path.basename(path)}")
        product = analyze_photo(path)
        print(f"  Erkannt: {product['product_name']}")

        listing = generate_listing(product, season)
        output.save_etsy_listing(product["product_name"], listing["raw"])
        csv_rows.append({
            "Produktname": product["product_name"],
            "Titel": listing["title"],
            "Beschreibung": listing["description"],
            "Tags": ", ".join(listing["tags"]),
        })

        caption = generate_caption(product, season)
        output.save_instagram_caption(product["product_name"], caption)
        short_text = product["product_name"] + " — vo Herz'n"
        img = create_post_image(short_text)
        output.save_instagram_image(product["product_name"], img)

        summary.append(f"{product['product_name']}: Etsy + Instagram erstellt")

    output.save_etsy_csv(csv_rows)
    output.save_summary(summary)
    print(f"\nAlle {len(paths)} Produkte verarbeitet!")
    print(f"Gespeichert in: {output.root}")


def main():
    print_header()

    while True:
        print_menu()
        choice = input("Deine Wahl: ").strip()

        if choice == "1":
            process_single("both")
        elif choice == "2":
            process_batch()
        elif choice == "3":
            process_single("etsy")
        elif choice == "4":
            process_single("instagram")
        elif choice == "5":
            print("\nServus! Bis zum naechsten Mal.")
            break
        else:
            print("Ungueltige Eingabe, bitte 1-5 waehlen.")


if __name__ == "__main__":
    main()
```

**Step 2: Manual test**

Run: `python3 cli.py`
Expected: Menu appears, option 5 exits cleanly

**Step 3: Commit**

```bash
git add cli.py
git commit -m "feat: add CLI tool for Mama"
```

---

### Task 8: Claude Code Skill (vo-herzn.md)

**Files:**
- Create: `skills/vo-herzn.md`

**Step 1: Create skill file**

```markdown
---
name: vo-herzn
description: Use when creating Etsy listings, Instagram posts, or any content for the Vo Herz'n handmade shop. Triggers on: Etsy, Instagram, Produktbeschreibung, Listing, Caption, Vo Herzn, Produktfoto.
---

# Vo Herz'n Content Creator

Du hilfst beim Erstellen von Inhalten fuer den Etsy-Shop "Vo Herz'n" — einen kleinen bayerischen Handmade-Shop fuer Deko, Accessoires, Taschen und Unikate.

## Workflow

1. **Frage was erstellt werden soll:** Etsy-Listing, Instagram-Post, oder beides?
2. **Produkt-Input holen:** Foto (Pfad) oder Textbeschreibung
3. **Module aufrufen:** Fuehre die Python-Module im Projektordner aus:

### Einzelnes Produkt

```bash
cd /Users/juu777/vo-herzn-projekt
python3 -c "
from voherzn.vision import analyze_photo, analyze_from_text
from voherzn.season import get_season_context
from voherzn.etsy import generate_listing
from voherzn.instagram import generate_caption, create_post_image
from voherzn.output import OutputManager

# Foto analysieren:
product = analyze_photo('PFAD_ZUM_FOTO')
# ODER aus Text:
# product = analyze_from_text('BESCHREIBUNG')

season = get_season_context()
output = OutputManager()

# Etsy
listing = generate_listing(product, season)
output.save_etsy_listing(product['product_name'], listing['raw'])

# Instagram
caption = generate_caption(product, season)
output.save_instagram_caption(product['product_name'], caption)
img = create_post_image(product['product_name'] + ' — vo Herz\\'n')
output.save_instagram_image(product['product_name'], img)

output.save_summary([f'{product[\"product_name\"]}: Etsy + Instagram erstellt'])
print(f'Output: {output.root}')
"
```

### Batch (mehrere Fotos)

```bash
cd /Users/juu777/vo-herzn-projekt
python3 cli.py
# Option 2 waehlen
```

## Tonalitaet

- Bayerisch-warm, authentisch, persoenlich
- Wie von einer Freundin erzaehlt
- Handmade-Charakter betonen
- "Vo Herz'n" = "von Herzen"

## Saisonale Hinweise

Pruefe immer den saisonalen Kontext und weise den User darauf hin:
- "Muttertag ist in X Tagen — soll ich die Texte darauf anpassen?"
- "Weihnachtszeit — ich baue adventliche Stimmung ein"

## Nach der Erstellung

- Zeige dem User die generierten Texte
- Frage ob Anpassungen gewuenscht sind ("mehr bayerisch", "kuerzere Beschreibung", etc.)
- Weise auf den Output-Ordner auf dem Desktop hin
```

**Step 2: Commit**

```bash
mkdir -p skills
git add skills/vo-herzn.md
git commit -m "feat: add Claude Code skill for Vo Herzn workflow"
```

---

### Task 9: Cleanup — alte Scripts loeschen

**Files:**
- Delete: `etsy_generator.py`
- Delete: `instagram_post.py`
- Delete: `create_logo.py`
- Delete: `hallo.py`

**Step 1: Delete old files**

```bash
rm etsy_generator.py instagram_post.py create_logo.py hallo.py
```

**Step 2: Verify nothing is broken**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove old standalone scripts, replaced by voherzn package"
```

---

### Task 10: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update project docs**

```markdown
# Projekt: Vo Herzn Automatisierung

## Zweck
Automatisiert Inhalte fuer den Vo Herz'n Handmade-Shop (Etsy + Instagram).

## Struktur
- `voherzn/` — Python-Package (vision, season, etsy, instagram, output)
- `cli.py` — CLI-Tool fuer Mama
- `skills/vo-herzn.md` — Claude Code Skill
- `website/` — Landing Page

## Stil
Deutsch, warm, bayerisch-freundlich

## Regeln
- Keine API-Keys direkt in Code
- Immer Fehlerbehandlung einbauen
- Vision: claude-sonnet-4-6, Text: claude-opus-4-6
- Output immer auf Desktop: ~/Desktop/Vo Herzn Output/
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with new project structure"
```
