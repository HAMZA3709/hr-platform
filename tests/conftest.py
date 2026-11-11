"""Fixtures pytest partagées : base SQLite temporaire, override de settings."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_hr_pipeline.db")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("AUDIT_PSEUDONYMIZATION_SALT", "test-salt")
os.environ.setdefault("LLM_PROVIDER", "none")
os.environ.setdefault("OPENMETADATA_ENABLED", "false")


@pytest.fixture(scope="session", autouse=True)
def _clean_db_file():
    db_path = "./test_hr_pipeline.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    yield
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture()
def db_session():
    from app.db.session import SessionLocal, init_db

    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        # Nettoie les données entre tests pour éviter les collisions candidate_ref
        from app.db.models import (
            AgentExecution,
            AuditEvent,
            Candidate,
            CandidateSkill,
            InterviewPreparationRow,
            JobOffer,
            OnboardingDecisionRow,
            PipelineRun,
            ScoringResultRow,
            ScreeningResultRow,
        )

        for model in (
            AuditEvent,
            AgentExecution,
            InterviewPreparationRow,
            OnboardingDecisionRow,
            ScoringResultRow,
            ScreeningResultRow,
            PipelineRun,
            CandidateSkill,
            Candidate,
            JobOffer,
        ):
            session.query(model).delete()
        session.commit()
        session.close()
