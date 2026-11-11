"""Tests d'authentification par clé API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(_clean_db_file):
    with TestClient(app) as c:
        yield c


def test_missing_api_key_returns_401(client):
    r = client.get("/api/v1/candidates")
    assert r.status_code == 401
    assert r.json()["error_code"] == "unauthorized"


def test_wrong_api_key_returns_401(client):
    r = client.get("/api/v1/candidates", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


def test_correct_api_key_succeeds(client):
    r = client.get("/api/v1/candidates", headers={"X-API-Key": "test-api-key"})
    assert r.status_code == 200


def test_health_endpoint_does_not_require_api_key(client):
    r = client.get("/health")
    assert r.status_code == 200
