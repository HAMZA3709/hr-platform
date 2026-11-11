"""Tests d'intégration API — candidats, lancement de pipeline, pagination."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "test-api-key"}


@pytest.fixture()
def client(_clean_db_file):
    with TestClient(app) as c:
        yield c


def test_create_candidate(client):
    r = client.post(
        "/api/v1/candidates",
        json={"candidate_ref": "api-int-1", "years_experience": 5, "skills": ["python"]},
        headers=HEADERS,
    )
    assert r.status_code == 201
    assert r.json()["candidate_ref"] == "api-int-1"


def test_create_candidate_duplicate_ref_fails(client):
    payload = {"candidate_ref": "api-int-dup", "years_experience": 5, "skills": []}
    r1 = client.post("/api/v1/candidates", json=payload, headers=HEADERS)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/candidates", json=payload, headers=HEADERS)
    assert r2.status_code == 422


def test_get_candidate_not_found(client):
    r = client.get("/api/v1/candidates/999999", headers=HEADERS)
    assert r.status_code == 404
    assert r.json()["error_code"] == "not_found"


def test_list_candidates_pagination(client):
    for i in range(3):
        client.post(
            "/api/v1/candidates",
            json={"candidate_ref": f"api-page-{i}", "years_experience": 1, "skills": []},
            headers=HEADERS,
        )
    r = client.get("/api/v1/candidates", params={"limit": 2}, headers=HEADERS)
    assert r.status_code == 200
    assert len(r.json()) <= 2


def test_full_pipeline_via_api(client):
    r = client.post(
        "/api/v1/candidates",
        json={
            "candidate_ref": "api-full-pipeline",
            "years_experience": 8,
            "skills": ["python", "sql", "leadership"],
        },
        headers=HEADERS,
    )
    candidate_id = r.json()["id"]

    r = client.post(f"/api/v1/candidates/{candidate_id}/run-pipeline", headers=HEADERS)
    assert r.status_code == 201
    assert r.json()["status"] == "success"
    run_id = r.json()["run_id"]

    r = client.get(f"/api/v1/pipeline-runs/{run_id}", headers=HEADERS)
    assert r.status_code == 200

    r = client.get("/api/v1/decisions", headers=HEADERS)
    assert r.status_code == 200
    assert any(d["ready"] for d in r.json())


def test_run_pipeline_candidate_not_found(client):
    r = client.post("/api/v1/candidates/999999/run-pipeline", headers=HEADERS)
    assert r.status_code == 404
