"""Tests des endpoints /health, /health/database, /health/openmetadata."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(_clean_db_file):
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_database(client):
    r = client.get("/health/database")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_openmetadata_disabled_by_default(client):
    r = client.get("/health/openmetadata")
    assert r.status_code == 200
    assert r.json()["status"] == "disabled"
