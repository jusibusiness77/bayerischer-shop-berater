"""Etsy OAuth 2.0 (PKCE) - Auth-URL, Token-Tausch, .env-Speicherung."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
USER_URL = "https://openapi.etsy.com/v3/application/users/{user_id}"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate_pkce_pair() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def build_auth_url(client_id: str, redirect_uri: str, scopes: str, state: str, code_challenge: str) -> str:
    from urllib.parse import urlencode
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(client_id: str, redirect_uri: str, code: str, code_verifier: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": code_verifier,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_shop_id(client_id: str, access_token: str) -> str | None:
    user_id = access_token.split(".", 1)[0]
    if not user_id.isdigit():
        return None
    response = requests.get(
        USER_URL.format(user_id=user_id),
        headers={"x-api-key": client_id, "Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if response.status_code != 200:
        return None
    shop_id = response.json().get("shop_id")
    return str(shop_id) if shop_id else None


def update_env(values: dict) -> None:
    """Schreibt/aktualisiert Keys in der .env, alle anderen Zeilen bleiben erhalten."""
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    seen: set[str] = set()
    for i, line in enumerate(lines):
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in values:
                lines[i] = f"{key}={values[key]}"
                seen.add(key)

    for key, value in values.items():
        if key not in seen:
            lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    load_dotenv(ENV_PATH, override=True)
