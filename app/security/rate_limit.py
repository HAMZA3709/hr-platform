"""
Limitation de débit simple, en mémoire, par clé API.

Suffisant pour un déploiement mono-instance / démo. Pour un déploiement
multi-instance en production, remplacez par un backend partagé (ex: Redis).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Header, Request

from app.core.config import get_settings
from app.core.errors import RateLimitedError

_hits: dict[str, deque] = defaultdict(deque)


async def enforce_rate_limit(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    key = x_api_key or (request.client.host if request.client else "unknown")
    now = time.monotonic()
    window = 60.0

    hits = _hits[key]
    while hits and now - hits[0] > window:
        hits.popleft()

    if len(hits) >= settings.rate_limit_per_minute:
        raise RateLimitedError("Trop de requêtes. Réessayez dans quelques instants.")

    hits.append(now)
