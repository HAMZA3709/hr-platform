"""
Client HTTP vers l'API FastAPI — le dashboard ne parle JAMAIS directement à
MySQL, uniquement à l'API (via requests), comme demandé.

Config via variables d'environnement :
    API_BASE_URL=http://localhost:8000
    API_KEY=<la même clé que celle configurée côté API>
"""

from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")


def _headers() -> dict:
    return {"X-API-Key": API_KEY}


def _handle_response(response: requests.Response):
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        st.error(f"Erreur API ({response.status_code}) : {detail}")
        return None
    return response.json()


def get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE_URL}{path}", headers=_headers(), params=params, timeout=10)
    except requests.RequestException as exc:
        st.error(f"Impossible de joindre l'API ({API_BASE_URL}) : {exc}")
        return None
    return _handle_response(r)


def post(path: str, json: dict | None = None):
    try:
        r = requests.post(f"{API_BASE_URL}{path}", headers=_headers(), json=json, timeout=30)
    except requests.RequestException as exc:
        st.error(f"Impossible de joindre l'API ({API_BASE_URL}) : {exc}")
        return None
    return _handle_response(r)
