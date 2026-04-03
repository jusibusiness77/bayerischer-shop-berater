#!/usr/bin/env python3
"""Instagram Post Generator für Vo Herz´n – mit Emoji-Support."""

import os
import math
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource

# --- Farben & Pfade ---
BG_COLOR  = "#FAF0F2"
ALTROSA   = "#C17A8A"
DUNKELROT = "#5C2D3A"
FONT_DIR  = os.path.expanduser("~/.voherzn_fonts")
DESKTOP   = os.path.expanduser("~/Desktop")
SIZE      = 1080


def load_font(filename, size):
    path = os.path.join(FONT_DIR, filename)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_heart(draw, cx, cy, size, color):
    points = []
    for i in range(201):
        t = 2 * math.pi * i / 200
        x = size * 16 * math.sin(t) ** 3
        y = -size * (13 * math.cos(t) - 5 * math.cos(2*t)
                     - 2 * math.cos(3*t) - math.cos(4*t))
        points.append((cx + x, cy + y))
    draw.polygon(points, fill=color)


def wrap_text(pilmoji, text, font, max_width):
    """Bricht Text mit Emoji-bewusster Breitenmessung um."""
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


def create_post(post_text: str) -> str:
    img  = Image.new("RGB", (SIZE, SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Fonts laden
    font_brand   = load_font("GreatVibes-Regular.ttf", 72)
    font_post    = load_font("Lato-Light.ttf", 52)
    font_footer1 = load_font("Lato-Regular.ttf", 26)
    font_footer2 = load_font("Lato-Light.ttf", 20)

    # --- Rahmen ---
    m = 32
    draw.rectangle([m, m, SIZE-m, SIZE-m], outline=ALTROSA, width=1)
    draw.rectangle([m+8, m+8, SIZE-m-8, SIZE-m-8], outline=ALTROSA, width=1)

    # ── OBEN: Branding ──────────────────────────────────────────────
    brand_text = "Vo Herz´n"
    bw = draw.textlength(brand_text, font=font_brand)
    draw.text(((SIZE - bw) / 2, 58), brand_text, font=font_brand, fill=DUNKELROT)
    draw_heart(draw, SIZE // 2 - int(bw) // 2 - 38, 97, 1.6, ALTROSA)

    # Zierlinie unter Branding
    line_w = 400
    lx     = (SIZE - line_w) // 2
    ly     = 155
    mid    = SIZE // 2
    draw.line([(lx, ly), (lx + line_w, ly)], fill=ALTROSA, width=1)
    draw.polygon([(mid, ly-5), (mid+5, ly), (mid, ly+5), (mid-5, ly)], fill=ALTROSA)

    # ── MITTE: Post-Text mit Emoji-Support ──────────────────────────
    max_w = SIZE - 160
    text_area_top = ly + 40
    text_area_bot = SIZE - 200

    with Pilmoji(img, source=GoogleEmojiSource) as pilmoji:
        lines = wrap_text(pilmoji, post_text, font_post, max_w)

        # Zeilenhöhe anhand Textbbox bestimmen
        sample_bbox = draw.textbbox((0, 0), "Ag", font=font_post)
        line_h  = (sample_bbox[3] - sample_bbox[1]) + 18
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

    # Dekoherz links oben im Textbereich
    draw_heart(draw, 90, text_area_top + 30, 2.0, ALTROSA)

    # ── UNTEN: Footer ───────────────────────────────────────────────
    fly = SIZE - 175
    draw.line([(lx, fly), (lx + line_w, fly)], fill=ALTROSA, width=1)
    draw.polygon([(mid, fly-5), (mid+5, fly), (mid, fly+5), (mid-5, fly)], fill=ALTROSA)

    fw1 = draw.textlength("hand´gmacht mit Liebe", font=font_footer1)
    draw.text(((SIZE - fw1) / 2, fly + 18), "hand´gmacht mit Liebe",
              font=font_footer1, fill=ALTROSA)

    foot2 = "DEKO  ·  GRAVUR  ·  UNIKATE  ·  BAYERN"
    fw2 = draw.textlength(foot2, font=font_footer2)
    draw.text(((SIZE - fw2) / 2, fly + 56), foot2, font=font_footer2, fill=DUNKELROT)

    # --- Speichern ---
    today    = date.today().strftime("%Y-%m-%d")
    filename = f"post_{today}.png"
    output   = os.path.join(DESKTOP, filename)
    counter  = 1
    while os.path.exists(output):
        filename = f"post_{today}_{counter}.png"
        output   = os.path.join(DESKTOP, filename)
        counter += 1

    img.save(output, "PNG")
    return output


def main():
    print("╔══════════════════════════════════════╗")
    print("║  Vo Herz´n – Instagram Post Creator   ║")
    print("╚══════════════════════════════════════╝\n")
    print("Gib deinen Post-Text ein (Enter = neue Zeile, leere Zeile = fertig):\n")

    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)

    post_text = " ".join(lines).strip()
    if not post_text:
        print("Kein Text eingegeben. Abbruch.")
        return

    print("\nErstelle Bild...")
    try:
        path = create_post(post_text)
        print(f"\n✓ Gespeichert: {path}")
    except Exception as e:
        print(f"\nFehler: {e}")


if __name__ == "__main__":
    main()
