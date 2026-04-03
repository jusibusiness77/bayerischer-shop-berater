"""Instagram Caption & Post-Image Generator fuer Vo Herz'n."""

import math
import os

import anthropic
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource

BG_COLOR = "#FAF0F2"
ALTROSA = "#C17A8A"
DUNKELROT = "#5C2D3A"
FONT_DIR = os.path.expanduser("~/.voherzn_fonts")
SIZE = 1080

REQUIRED_HASHTAGS = ["#voherzn", "#handgemacht", "#bayern", "#handmade"]

CAPTION_PROMPT = """Du bist der Social-Media-Texter fuer den Handmade-Shop "Vo Herz'n" aus Bayern.
Schreibe eine Instagram-Caption im bayerisch-warmen Ton.

Produkt:
- Name: {product_name}
- Kategorie: {category}
- Materialien: {materials}
- Farben: {colors}
- Merkmale: {features}

Saison-Kontext:
- Saison: {season}
- Events: {events}
- Stimmung: {mood}
- Keywords: {keywords}

Regeln:
- 3-5 kurze Absaetze
- Warmer, herzlicher Ton
- Genau 30 Hashtags am Ende
- Pflicht-Hashtags: {required_hashtags}
- Saisonale Hashtags einbauen: {seasonal_hashtags}
"""


def _get_client() -> anthropic.Anthropic:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden")
    return anthropic.Anthropic(api_key=api_key)


def _load_font(filename: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONT_DIR, filename)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def generate_caption(product: dict, season: dict) -> str:
    prompt = CAPTION_PROMPT.format(
        product_name=product.get("product_name", ""),
        category=product.get("category", ""),
        materials=", ".join(product.get("materials", [])),
        colors=", ".join(product.get("colors", [])),
        features=", ".join(product.get("features", [])),
        season=season.get("season", ""),
        events=", ".join(season.get("events", [])),
        mood=season.get("mood", ""),
        keywords=", ".join(season.get("keywords", [])),
        required_hashtags=" ".join(REQUIRED_HASHTAGS),
        seasonal_hashtags=" ".join(season.get("hashtags", [])),
    )

    client = _get_client()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _draw_heart(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: float, color: str):
    points = []
    for i in range(201):
        t = 2 * math.pi * i / 200
        x = size * 16 * math.sin(t) ** 3
        y = -size * (
            13 * math.cos(t)
            - 5 * math.cos(2 * t)
            - 2 * math.cos(3 * t)
            - math.cos(4 * t)
        )
        points.append((cx + x, cy + y))
    draw.polygon(points, fill=color)


def _wrap_text(pilmoji, text: str, font, max_width: int) -> list[str]:
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


def create_post_image(post_text: str) -> Image.Image:
    img = Image.new("RGB", (SIZE, SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_brand = _load_font("GreatVibes-Regular.ttf", 72)
    font_post = _load_font("Lato-Light.ttf", 52)
    font_footer1 = _load_font("Lato-Regular.ttf", 26)
    font_footer2 = _load_font("Lato-Light.ttf", 20)

    # Doppelrahmen
    m = 32
    draw.rectangle([m, m, SIZE - m, SIZE - m], outline=ALTROSA, width=1)
    draw.rectangle([m + 8, m + 8, SIZE - m - 8, SIZE - m - 8], outline=ALTROSA, width=1)

    # Branding
    brand_text = "Vo Herz\u00b4n"
    bw = draw.textlength(brand_text, font=font_brand)
    draw.text(((SIZE - bw) / 2, 58), brand_text, font=font_brand, fill=DUNKELROT)
    _draw_heart(draw, SIZE // 2 - int(bw) // 2 - 38, 97, 1.6, ALTROSA)

    # Zierlinie unter Branding
    line_w = 400
    lx = (SIZE - line_w) // 2
    ly = 155
    mid = SIZE // 2
    draw.line([(lx, ly), (lx + line_w, ly)], fill=ALTROSA, width=1)
    draw.polygon(
        [(mid, ly - 5), (mid + 5, ly), (mid, ly + 5), (mid - 5, ly)], fill=ALTROSA
    )

    # Post-Text mit Emoji-Support
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
                line,
                font=font_post,
                fill=DUNKELROT,
                emoji_scale_factor=1.1,
            )

    # Dekoherz
    _draw_heart(draw, 90, text_area_top + 30, 2.0, ALTROSA)

    # Footer
    fly = SIZE - 175
    draw.line([(lx, fly), (lx + line_w, fly)], fill=ALTROSA, width=1)
    draw.polygon(
        [(mid, fly - 5), (mid + 5, fly), (mid, fly + 5), (mid - 5, fly)], fill=ALTROSA
    )

    fw1 = draw.textlength("hand\u00b4gmacht mit Liebe", font=font_footer1)
    draw.text(
        ((SIZE - fw1) / 2, fly + 18),
        "hand\u00b4gmacht mit Liebe",
        font=font_footer1,
        fill=ALTROSA,
    )

    foot2 = "DEKO  \u00b7  GRAVUR  \u00b7  UNIKATE  \u00b7  BAYERN"
    fw2 = draw.textlength(foot2, font=font_footer2)
    draw.text(((SIZE - fw2) / 2, fly + 56), foot2, font=font_footer2, fill=DUNKELROT)

    return img
