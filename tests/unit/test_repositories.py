"""Tests des repositories (accès DB)."""

from __future__ import annotations

import pytest

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.pipeline_repository import PipelineRunRepository


def test_candidate_repository_create_and_get(db_session):
    repo = CandidateRepository(db_session)
    candidate = repo.create(
        candidate_ref="repo-test-1", years_experience=5, skills=["python", "sql"]
    )
    assert candidate.id is not None
    assert candidate.pseudonymized_ref != "repo-test-1"

    fetched = repo.get_by_id(candidate.id)
    assert fetched.candidate_ref == "repo-test-1"
    assert {s.skill_name for s in fetched.skills} == {"python", "sql"}


def test_candidate_repository_get_by_ref(db_session):
    repo = CandidateRepository(db_session)
    repo.create(candidate_ref="repo-test-2", years_experience=3, skills=[])
    found = repo.get_by_ref("repo-test-2")
    assert found is not None
    assert repo.get_by_ref("nonexistent-ref") is None


def test_candidate_repository_list_pagination(db_session):
    repo = CandidateRepository(db_session)
    for i in range(5):
        repo.create(candidate_ref=f"repo-page-{i}", years_experience=1, skills=[])

    items, total = repo.list(offset=0, limit=2)
    assert len(items) == 2
    assert total == 5


def test_pipeline_run_repository_create_and_finalize(db_session):
    candidate_repo = CandidateRepository(db_session)
    candidate = candidate_repo.create(candidate_ref="repo-run-1", years_experience=5, skills=[])

    run_repo = PipelineRunRepository(db_session)
    run = run_repo.create(run_id="run-repo-1", candidate_id=candidate.id, correlation_id="corr-1")
    assert run.status == "running"

    finalized = run_repo.finalize(run, status="success", duration_ms=123.4)
    assert finalized.status == "success"
    assert finalized.ended_at is not None


def test_pipeline_run_repository_get_by_run_id(db_session):
    candidate_repo = CandidateRepository(db_session)
    candidate = candidate_repo.create(candidate_ref="repo-run-2", years_experience=5, skills=[])

    run_repo = PipelineRunRepository(db_session)
    run_repo.create(run_id="run-repo-2", candidate_id=candidate.id, correlation_id="corr-2")

    found = run_repo.get_by_run_id("run-repo-2")
    assert found is not None
    assert run_repo.get_by_run_id("nonexistent") is None
