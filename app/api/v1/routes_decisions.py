"""Routes /api/v1/decisions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.repositories.pipeline_repository import DecisionRepository
from app.schemas.candidate import DecisionOut
from app.security.api_key import verify_api_key
from app.security.rate_limit import enforce_rate_limit

router = APIRouter(
    prefix="/decisions",
    tags=["decisions"],
    dependencies=[Depends(verify_api_key), Depends(enforce_rate_limit)],
)


def _to_out(decision) -> DecisionOut:
    return DecisionOut.model_validate(decision)


@router.get("", response_model=list[DecisionOut])
def list_decisions(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[DecisionOut]:
    decisions, _total = DecisionRepository(db).list(offset=offset, limit=limit)
    return [_to_out(d) for d in decisions]


@router.get("/{decision_id}", response_model=DecisionOut)
def get_decision(decision_id: int, db: Session = Depends(get_db)) -> DecisionOut:
    decision = DecisionRepository(db).get_by_id(decision_id)
    if decision is None:
        raise NotFoundError(f"Décision {decision_id} introuvable.")
    return _to_out(decision)
