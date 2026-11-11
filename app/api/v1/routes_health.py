"""Routes /health, /health/database, /health/openmetadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/database")
def health_database(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}


@router.get("/health/openmetadata")
def health_openmetadata() -> dict:
    settings = get_settings()
    if not settings.openmetadata_enabled:
        return {"status": "disabled"}

    try:
        from app.openmetadata.client import get_client

        client = get_client()
        healthy = client.health_check()
        return {"status": "ok" if healthy else "unreachable"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}
