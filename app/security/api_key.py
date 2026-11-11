"""Authentification par clé API (header X-API-Key)."""

from __future__ import annotations

from fastapi import Header

from app.core.config import get_settings
from app.core.errors import UnauthorizedError


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_api_key is None or x_api_key != settings.api_key:
        raise UnauthorizedError("Clé API manquante ou invalide (header X-API-Key).")
