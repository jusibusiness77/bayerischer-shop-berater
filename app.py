"""Vo Herz'n — Flask Backend fuer Etsy Listing Generator."""

import base64
import json
import os
import tempfile

from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from voherzn.vision import analyze_photo
from voherzn.season import get_season_context
from voherzn.etsy import generate_listing

app = Flask(__name__, static_folder="website", static_url_path="")


@app.route("/")
def index():
    return send_from_directory("website", "index.html")


@app.route("/api/season")
def season():
    ctx = get_season_context()
    return jsonify(ctx)


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data or "images" not in data:
        return jsonify({"error": "Keine Bilder gesendet"}), 400

    images = data["images"][:10]
    season = get_season_context()
    results = []

    for i, img_data in enumerate(images):
        try:
            # Base64 Bild in temporaere Datei schreiben
            header, encoded = img_data["data"].split(",", 1) if "," in img_data["data"] else ("", img_data["data"])
            image_bytes = base64.b64decode(encoded)

            ext = ".jpg"
            if "png" in img_data.get("type", ""):
                ext = ".png"
            elif "webp" in img_data.get("type", ""):
                ext = ".webp"

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name

            try:
                product = analyze_photo(tmp_path)
                listing = generate_listing(product, season)
                results.append({
                    "index": i,
                    "filename": img_data.get("name", f"Bild {i+1}"),
                    "product": product,
                    "listing": listing,
                    "season": season,
                })
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            results.append({
                "index": i,
                "filename": img_data.get("name", f"Bild {i+1}"),
                "error": str(e),
            })

    return jsonify({"results": results, "season": season})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
