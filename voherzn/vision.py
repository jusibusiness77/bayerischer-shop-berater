import base64
import json
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

VISION_PROMPT = """Analysiere dieses Produktfoto und gib die Informationen als JSON zurueck.
Antworte NUR mit dem JSON, ohne weitere Erklaerung.

Format:
{
    "product_name": "Name des Produkts",
    "category": "Deko | Tasche | Accessoire | Gravur | Unikat",
    "materials": ["Material 1", "Material 2"],
    "colors": ["Farbe 1", "Farbe 2"],
    "features": ["Merkmal 1", "Merkmal 2", "Merkmal 3"]
}"""

TEXT_PROMPT = """Erstelle Produktdaten aus dieser Beschreibung und gib sie als JSON zurueck.
Antworte NUR mit dem JSON, ohne weitere Erklaerung.

Beschreibung: {description}

Format:
{{
    "product_name": "Name des Produkts",
    "category": "Deko | Tasche | Accessoire | Gravur | Unikat",
    "materials": ["Material 1", "Material 2"],
    "colors": ["Farbe 1", "Farbe 2"],
    "features": ["Merkmal 1", "Merkmal 2", "Merkmal 3"]
}}"""


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden")
    return anthropic.Anthropic(api_key=api_key)


def _encode_image(photo_path: str) -> tuple[str, str]:
    ext = os.path.splitext(photo_path)[1].lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")

    with open(photo_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _extract_json(text: str) -> dict:
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if md_match:
        text = md_match.group(1)
    return json.loads(text.strip())


def analyze_photo(photo_path: str) -> dict:
    client = _get_client()
    image_data, media_type = _encode_image(photo_path)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }
        ],
    )

    return _extract_json(message.content[0].text)


def analyze_photos(photo_paths: list[str]) -> list[dict]:
    paths = photo_paths[:10]
    results = []
    for path in paths:
        result = analyze_photo(path)
        result["source_photo"] = path
        results.append(result)
    return results


def analyze_from_text(description: str) -> dict:
    client = _get_client()

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": TEXT_PROMPT.format(description=description),
            }
        ],
    )

    return _extract_json(message.content[0].text)
