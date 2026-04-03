from __future__ import annotations

import csv
import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

DEFAULT_BASE = os.path.expanduser("~/Desktop/Vo Herzn Output")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class OutputManager:
    def __init__(self, base_dir: str = DEFAULT_BASE, d: date | None = None):
        if d is None:
            d = date.today()
        date_str = d.isoformat()
        root = os.path.join(base_dir, date_str)

        if os.path.exists(root):
            counter = 1
            while os.path.exists(f"{root}_{counter}"):
                counter += 1
            root = f"{root}_{counter}"

        self._root = root
        self._etsy_dir = os.path.join(root, "etsy")
        self._instagram_dir = os.path.join(root, "instagram")

        os.makedirs(self._etsy_dir, exist_ok=True)
        os.makedirs(self._instagram_dir, exist_ok=True)

    @property
    def root(self) -> str:
        return self._root

    @property
    def etsy_dir(self) -> str:
        return self._etsy_dir

    @property
    def instagram_dir(self) -> str:
        return self._instagram_dir

    def save_etsy_listing(self, product_name: str, content: str) -> str:
        slug = _slugify(product_name)
        path = os.path.join(self._etsy_dir, f"{slug}-listing.txt")
        Path(path).write_text(content, encoding="utf-8")
        return path

    def save_etsy_csv(self, rows: list[dict]) -> str:
        path = os.path.join(self._etsy_dir, "alle-listings.csv")
        if not rows:
            Path(path).write_text("", encoding="utf-8")
            return path
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def save_instagram_caption(self, product_name: str, caption: str) -> str:
        slug = _slugify(product_name)
        path = os.path.join(self._instagram_dir, f"{slug}-caption.txt")
        Path(path).write_text(caption, encoding="utf-8")
        return path

    def save_instagram_image(self, product_name: str, image) -> str:
        slug = _slugify(product_name)
        path = os.path.join(self._instagram_dir, f"{slug}-post.png")
        image.save(path)
        return path

    def save_summary(self, entries: list[str]) -> str:
        path = os.path.join(self._root, "zusammenfassung.txt")
        Path(path).write_text("\n".join(entries), encoding="utf-8")
        return path
