"""Accès DB pour les exécutions de pipeline et leurs résultats détaillés."""

from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AgentExecution,
    InterviewPreparationRow,
    OnboardingDecisionRow,
    PipelineRun,
    ScoringResultRow,
    ScreeningResultRow,
)


class PipelineRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, run_id: str, candidate_id: int, correlation_id: str) -> PipelineRun:
        run = PipelineRun(
            run_id=run_id,
            candidate_id=candidate_id,
            correlation_id=correlation_id,
            status="running",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_run_id(self, run_id: str) -> PipelineRun | None:
        stmt = select(PipelineRun).where(PipelineRun.run_id == run_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20) -> tuple[list[PipelineRun], int]:
        total = self.db.execute(select(PipelineRun)).scalars().all()
        stmt = select(PipelineRun).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, len(total)

    def finalize(self, run: PipelineRun, status: str, duration_ms: float) -> PipelineRun:
        from datetime import datetime

        run.status = status
        run.duration_ms = duration_ms
        run.ended_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(run)
        return run

    def add_agent_execution(
        self,
        run: PipelineRun,
        agent_name: str,
        status: str,
        duration_ms: float,
        tokens_in: int,
        tokens_out: int,
        llm_provider: str,
        error_message: str | None = None,
    ) -> AgentExecution:
        execution = AgentExecution(
            pipeline_run_id=run.id,
            agent_name=agent_name,
            status=status,
            duration_ms=duration_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            llm_provider=llm_provider,
            error_message=error_message,
        )
        self.db.add(execution)
        self.db.commit()
        return execution

    def save_screening_result(self, run: PipelineRun, **kwargs) -> ScreeningResultRow:
        row = ScreeningResultRow(pipeline_run_id=run.id, **kwargs)
        self.db.add(row)
        self.db.commit()
        return row

    def save_scoring_result(self, run: PipelineRun, **kwargs) -> ScoringResultRow:
        row = ScoringResultRow(pipeline_run_id=run.id, **kwargs)
        self.db.add(row)
        self.db.commit()
        return row

    def save_interview_preparation(self, run: PipelineRun, **kwargs) -> InterviewPreparationRow:
        row = InterviewPreparationRow(pipeline_run_id=run.id, **kwargs)
        self.db.add(row)
        self.db.commit()
        return row

    def save_onboarding_decision(self, run: PipelineRun, **kwargs) -> OnboardingDecisionRow:
        row = OnboardingDecisionRow(pipeline_run_id=run.id, **kwargs)
        self.db.add(row)
        self.db.commit()
        return row


class DecisionRepository:
    """Accès en lecture aux décisions d'onboarding (endpoint /decisions)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, decision_id: int) -> OnboardingDecisionRow | None:
        return self.db.get(OnboardingDecisionRow, decision_id)

    def list(self, offset: int = 0, limit: int = 20) -> tuple[list[OnboardingDecisionRow], int]:
        total = self.db.execute(select(OnboardingDecisionRow)).scalars().all()
        stmt = select(OnboardingDecisionRow).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, len(total)
