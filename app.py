"""Vo Herz'n — Flask Backend fuer Etsy Listing Generator."""

import base64
import json
import os
import secrets
import tempfile

from pathlib import Path
from flask import Flask, jsonify, redirect, request, send_from_directory, session
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from voherzn.vision import analyze_photo
from voherzn.season import get_season_context
from voherzn.etsy import generate_listing
from voherzn import etsy_auth
from voherzn.etsy_post import post_listing_to_etsy

app = Flask(__name__, static_folder="website", static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)


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


# --- Etsy OAuth ---

@app.route("/auth/etsy")
def auth_etsy():
    client_id = os.environ.get("ETSY_API_KEY")
    redirect_uri = os.environ.get("ETSY_REDIRECT_URI")
    scopes = os.environ.get("ETSY_SCOPES", "listings_w listings_r shops_r")
    if not client_id or not redirect_uri:
        return jsonify({"error": "ETSY_API_KEY oder ETSY_REDIRECT_URI fehlt in .env"}), 500

    verifier, challenge = etsy_auth.generate_pkce_pair()
    state = secrets.token_urlsafe(24)
    session["etsy_oauth_state"] = state
    session["etsy_oauth_verifier"] = verifier

    return redirect(etsy_auth.build_auth_url(client_id, redirect_uri, scopes, state, challenge))


@app.route("/auth/etsy/callback")
def auth_etsy_callback():
    error = request.args.get("error")
    if error:
        return f"<h1>Etsy Auth Fehler</h1><pre>{error}: {request.args.get('error_description', '')}</pre>", 400

    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return "<h1>Fehlende Parameter</h1><p>code oder state nicht vorhanden.</p>", 400
    if state != session.get("etsy_oauth_state"):
        return "<h1>Ungueltiger State</h1><p>CSRF-Schutz fehlgeschlagen.</p>", 400

    verifier = session.pop("etsy_oauth_verifier", None)
    session.pop("etsy_oauth_state", None)
    if not verifier:
        return "<h1>Session abgelaufen</h1><p>Bitte /auth/etsy erneut aufrufen.</p>", 400

    client_id = os.environ.get("ETSY_API_KEY")
    shared_secret = os.environ.get("ETSY_SHARED_SECRET", "")
    redirect_uri = os.environ.get("ETSY_REDIRECT_URI")

    try:
        token_data = etsy_auth.exchange_code_for_token(client_id, redirect_uri, code, verifier)
    except Exception as exc:
        return f"<h1>Token-Tausch fehlgeschlagen</h1><pre>{exc}</pre>", 500

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token", "")
    if not access_token:
        return f"<h1>Kein Access Token erhalten</h1><pre>{token_data}</pre>", 500

    shop_id = etsy_auth.fetch_shop_id(client_id, shared_secret, access_token) or ""

    etsy_auth.update_env({
        "ETSY_ACCESS_TOKEN": access_token,
        "ETSY_REFRESH_TOKEN": refresh_token,
        "ETSY_SHOP_ID": shop_id,
    })

    return (
        "<h1>Etsy verbunden</h1>"
        f"<p>Shop ID: <code>{shop_id or '(nicht ermittelt)'}</code></p>"
        "<p>Du kannst dieses Fenster schliessen und im Generator auf "
        "<strong>Auf Etsy posten</strong> klicken.</p>"
        "<script>setTimeout(() => window.close(), 1500);</script>"
    )


@app.route("/api/etsy/status")
def etsy_status():
    load_dotenv(Path(__file__).parent / ".env", override=True)
    connected = bool(os.environ.get("ETSY_ACCESS_TOKEN") and os.environ.get("ETSY_SHOP_ID"))
    return jsonify({"connected": connected, "shop_id": os.environ.get("ETSY_SHOP_ID", "")})


@app.route("/api/etsy/post", methods=["POST"])
def etsy_post():
    data = request.get_json() or {}
    listing = data.get("listing")
    if not listing or not listing.get("title"):
        return jsonify({"success": False, "error": "Listing-Daten fehlen"}), 400

    result = post_listing_to_etsy(listing, price=data.get("price"))
    status = 200 if result.get("success") else (401 if result.get("needs_auth") else 400)
    return jsonify(result), status


if __name__ == "__main__":
    app.run(debug=True, port=5001)
