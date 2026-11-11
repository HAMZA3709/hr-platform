"""Tests des métriques Prometheus — vérifie la présence des métriques et
l'absence de labels à forte cardinalité (candidate_id, run_id)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "test-api-key"}


@pytest.fixture()
def client(_clean_db_file):
    with TestClient(app) as c:
        yield c


def test_metrics_endpoint_exposes_prometheus_format(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]


def test_metrics_contain_expected_series_after_a_run(client):
    r = client.post(
        "/api/v1/candidates",
        json={"candidate_ref": "metrics-test-1", "years_experience": 8, "skills": ["python", "sql", "leadership"]},
        headers=HEADERS,
    )
    candidate_id = r.json()["id"]
    client.post(f"/api/v1/candidates/{candidate_id}/run-pipeline", headers=HEADERS)

    r = client.get("/metrics")
    body = r.text
    assert "hr_pipeline_runs_total" in body
    assert "hr_agent_executions_total" in body
    assert "hr_llm_tokens_total" in body


def test_metrics_never_expose_high_cardinality_labels(client):
    r = client.post(
        "/api/v1/candidates",
        json={"candidate_ref": "metrics-cardinality-test", "years_experience": 8, "skills": ["python"]},
        headers=HEADERS,
    )
    candidate_id = r.json()["id"]
    run_response = client.post(f"/api/v1/candidates/{candidate_id}/run-pipeline", headers=HEADERS)
    run_id = run_response.json()["run_id"]

    r = client.get("/metrics")
    assert "candidate_id" not in r.text
    assert run_id not in r.text
