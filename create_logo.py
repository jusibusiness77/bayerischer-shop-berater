#!/usr/bin/env python3
"""Erstellt das Vo Herzn Logo als PNG."""

import os
import math
import requests
from PIL import Image, ImageDraw, ImageFont

# --- Farben ---
BG_COLOR = "#FAF0F2"
ALTROSA = "#C17A8A"
DUNKELROT = "#5C2D3A"
DESKTOP = os.path.expanduser("~/Desktop")
OUTPUT = os.path.join(DESKTOP, "voherzn_logo.png")

FONT_DIR = os.path.expanduser("~/.voherzn_fonts")
os.makedirs(FONT_DIR, exist_ok=True)

FONTS = {
    "script": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/greatvibes/GreatVibes-Regular.ttf",
        "path": os.path.join(FONT_DIR, "GreatVibes-Regular.ttf"),
    },
    "caps": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Regular.ttf",
        "path": os.path.join(FONT_DIR, "Lato-Regular.ttf"),
    },
    "caps_light": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Light.ttf",
        "path": os.path.join(FONT_DIR, "Lato-Light.ttf"),
    },
}


def download_font(name, info):
    if os.path.exists(info["path"]):
        print(f"  Font '{name}' bereits vorhanden.")
        return True
    print(f"  Lade Font '{name}' herunter...")
    try:
        r = requests.get(info["url"], timeout=15)
        r.raise_for_status()
        with open(info["path"], "wb") as f:
            f.write(r.content)
        print(f"  ✓ '{name}' gespeichert.")
        return True
    except Exception as e:
        print(f"  ✗ Fehler beim Download von '{name}': {e}")
        return False


def load_font(key, size):
    path = FONTS[key]["path"]
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_heart(draw, cx, cy, size, color):
    """Zeichnet ein Herz mit mathematischer Kurve."""
    points = []
    steps = 200
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        x = size * 16 * math.sin(t) ** 3
        y = -size * (13 * math.cos(t) - 5 * math.cos(2 * t)
                     - 2 * math.cos(3 * t) - math.cos(4 * t))
        points.append((cx + x, cy + y))
    draw.polygon(points, fill=color)


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def main():
    print("Lade Schriften herunter...")
    for name, info in FONTS.items():
        download_font(name, info)

    print("Erstelle Logo...")
    W, H = 1200, 600
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Dezente Randlinie ---
    margin = 28
    border_color = ALTROSA
    draw.rectangle([margin, margin, W - margin, H - margin],
                   outline=border_color, width=1)
    draw.rectangle([margin + 6, margin + 6, W - margin - 6, H - margin - 6],
                   outline=border_color, width=1)

    # --- Herz ---
    heart_y = 158
    draw_heart(draw, W // 2, heart_y, 2.6, ALTROSA)

    # --- Haupttext "Vo Herzn" ---
    font_main = load_font("script", 148)
    text_main = "Vo Herz´n"
    bbox = draw.textbbox((0, 0), text_main, font=font_main)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (W - tw) // 2 - bbox[0]
    ty = heart_y + 28
    draw.text((tx, ty), text_main, font=font_main, fill=DUNKELROT)

    # --- Zierlinien ---
    line_y = ty + th + 28
    line_w = 320
    lx = (W - line_w) // 2
    draw.line([(lx, line_y), (lx + line_w, line_y)], fill=ALTROSA, width=1)
    # Kleine Raute in der Mitte
    mid = W // 2
    diamond = [(mid, line_y - 5), (mid + 5, line_y), (mid, line_y + 5), (mid - 5, line_y)]
    draw.polygon(diamond, fill=ALTROSA)

    # --- "HANDGEMACHT MIT LIEBE" ---
    font_sub1 = load_font("caps", 22)
    text_sub1 = "HAND´GMACHT  MIT  LIEBE"
    bbox2 = draw.textbbox((0, 0), text_sub1, font=font_sub1)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((W - tw2) // 2 - bbox2[0], line_y + 18),
              text_sub1, font=font_sub1, fill=ALTROSA)

    # --- "DEKO · GRAVUR · UNIKATE · BAYERN" ---
    font_sub2 = load_font("caps_light", 16)
    text_sub2 = "DEKO  ·  GRAVUR  ·  UNIKATE  ·  BAYERN"
    bbox3 = draw.textbbox((0, 0), text_sub2, font=font_sub2)
    tw3 = bbox3[2] - bbox3[0]
    sub2_y = line_y + 56
    draw.text(((W - tw3) // 2 - bbox3[0], sub2_y),
              text_sub2, font=font_sub2, fill=DUNKELROT)

    # --- Untere Zierlinie ---
    line_y2 = sub2_y + 30
    draw.line([(lx, line_y2), (lx + line_w, line_y2)], fill=ALTROSA, width=1)
    draw.polygon(
        [(mid, line_y2 - 5), (mid + 5, line_y2), (mid, line_y2 + 5), (mid - 5, line_y2)],
        fill=ALTROSA
    )

    img.save(OUTPUT, "PNG", dpi=(300, 300))
    print(f"\n✓ Logo gespeichert: {OUTPUT}")


if __name__ == "__main__":
    main()
