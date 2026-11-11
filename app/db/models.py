"""
Modèles SQLAlchemy du pipeline RH.

Tables : candidates, candidate_skills, job_offers, pipeline_runs,
agent_executions, screening_results, scoring_results,
interview_preparations, onboarding_decisions, audit_events.

Note RGPD : `candidates.pseudonymized_ref` est le seul identifiant utilisé
dans les logs d'audit et les métadonnées OpenMetadata — jamais `full_name`
ni `email` directement.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class JobOffer(Base):
    __tablename__ = "job_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    required_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    min_years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    candidates: Mapped[list[Candidate]] = relationship(back_populates="job_offer")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    pseudonymized_ref: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Champs non sensibles uniquement (le nom/email/téléphone ne sont PAS
    # persistés ici par défaut — voir app/schemas/candidate.py pour le détail
    # de ce qui est accepté en entrée mais volontairement absent du stockage
    # de démonstration, pour rester prudent par défaut sur le PII).
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)

    job_offer_id: Mapped[int | None] = mapped_column(ForeignKey("job_offers.id"), nullable=True)
    job_offer: Mapped[JobOffer | None] = relationship(back_populates="candidates")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    skills: Mapped[list[CandidateSkill]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[list[PipelineRun]] = relationship(back_populates="candidate")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="skills")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    # running | success | rejected_at_screening | error

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="pipeline_runs")
    agent_executions: Mapped[list[AgentExecution]] = relationship(
        back_populates="pipeline_run", cascade="all, delete-orphan"
    )
    screening_result: Mapped[ScreeningResultRow | None] = relationship(
        back_populates="pipeline_run", uselist=False, cascade="all, delete-orphan"
    )
    scoring_result: Mapped[ScoringResultRow | None] = relationship(
        back_populates="pipeline_run", uselist=False, cascade="all, delete-orphan"
    )
    interview_preparation: Mapped[InterviewPreparationRow | None] = relationship(
        back_populates="pipeline_run", uselist=False, cascade="all, delete-orphan"
    )
    onboarding_decision: Mapped[OnboardingDecisionRow | None] = relationship(
        back_populates="pipeline_run", uselist=False, cascade="all, delete-orphan"
    )


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # success | error
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="agent_executions")


class ScreeningResultRow(Base):
    __tablename__ = "screening_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), unique=True, nullable=False
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    matched_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rules_applied: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="screening_result")


class ScoringResultRow(Base):
    __tablename__ = "scoring_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), unique=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_component: Mapped[float] = mapped_column(Float, nullable=False)
    skills_component: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rules_applied: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="scoring_result")


class InterviewPreparationRow(Base):
    __tablename__ = "interview_preparations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), unique=True, nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by_llm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="interview_preparation")


class OnboardingDecisionRow(Base):
    __tablename__ = "onboarding_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), unique=True, nullable=False
    )
    ready: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rules_applied: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="onboarding_decision")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pseudonymized_ref: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    agent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_applied: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    fields_used: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
