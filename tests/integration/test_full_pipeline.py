"""Test d'intégration : un pipeline complet, de la création du candidat à la
décision d'onboarding, via l'API HTTP (pas d'appel direct aux services)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "test-api-key"}


def test_full_pipeline_success_path(db_session):
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/candidates",
            json={
                "candidate_ref": "full-pipeline-strong",
                "years_experience": 8,
                "skills": ["python", "sql", "leadership"],
            },
            headers=HEADERS,
        )
        assert r.status_code == 201
        candidate_id = r.json()["id"]

        r = client.post(f"/api/v1/candidates/{candidate_id}/run-pipeline", headers=HEADERS)
        assert r.status_code == 201
        run = r.json()
        assert run["status"] == "success"

        r = client.get(f"/api/v1/pipeline-runs/{run['run_id']}", headers=HEADERS)
        assert r.status_code == 200

        r = client.get("/api/v1/decisions", headers=HEADERS)
        assert r.status_code == 200
        decisions = r.json()
        assert any(d["ready"] for d in decisions)


def test_full_pipeline_rejected_at_screening(db_session):
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/candidates",
            json={
                "candidate_ref": "full-pipeline-weak",
                "years_experience": 0,
                "skills": ["excel"],
            },
            headers=HEADERS,
        )
        assert r.status_code == 201
        candidate_id = r.json()["id"]

        r = client.post(f"/api/v1/candidates/{candidate_id}/run-pipeline", headers=HEADERS)
        assert r.status_code == 201
        run = r.json()
        assert run["status"] == "rejected_at_screening"

        # Pas de décision d'onboarding pour ce run (arrêt anticipé)
        r = client.get(f"/api/v1/pipeline-runs/{run['run_id']}", headers=HEADERS)
        assert r.status_code == 200
