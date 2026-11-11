"""Routes /api/v1/candidates/{id}/run-pipeline et /api/v1/pipeline-runs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.repositories.pipeline_repository import PipelineRunRepository
from app.schemas.candidate import PipelineRunOut
from app.security.api_key import verify_api_key
from app.security.rate_limit import enforce_rate_limit
from app.services.pipeline_service import PipelineService

router = APIRouter(
    tags=["pipeline"],
    dependencies=[Depends(verify_api_key), Depends(enforce_rate_limit)],
)


def _to_out(run) -> PipelineRunOut:
    return PipelineRunOut.model_validate(run)


@router.post("/candidates/{candidate_id}/run-pipeline", response_model=PipelineRunOut, status_code=201)
def run_pipeline(candidate_id: int, request: Request, db: Session = Depends(get_db)) -> PipelineRunOut:
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    run = PipelineService(db).run_pipeline_for_candidate(candidate_id, correlation_id=correlation_id)
    return _to_out(run)


@router.get("/pipeline-runs", response_model=list[PipelineRunOut])
def list_pipeline_runs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[PipelineRunOut]:
    runs, _total = PipelineRunRepository(db).list(offset=offset, limit=limit)
    return [_to_out(r) for r in runs]


@router.get("/pipeline-runs/{run_id}", response_model=PipelineRunOut)
def get_pipeline_run(run_id: str, db: Session = Depends(get_db)) -> PipelineRunOut:
    run = PipelineRunRepository(db).get_by_run_id(run_id)
    if run is None:
        raise NotFoundError(f"Run {run_id} introuvable.")
    return _to_out(run)
