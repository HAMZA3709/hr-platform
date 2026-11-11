"""Routes /api/v1/candidates."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.candidate import CandidateCreate, CandidateOut
from app.security.api_key import verify_api_key
from app.security.rate_limit import enforce_rate_limit
from app.services.candidate_service import CandidateService

router = APIRouter(
    prefix="/candidates",
    tags=["candidates"],
    dependencies=[Depends(verify_api_key), Depends(enforce_rate_limit)],
)


def _to_out(candidate) -> CandidateOut:
    return CandidateOut(
        id=candidate.id,
        candidate_ref=candidate.candidate_ref,
        years_experience=candidate.years_experience,
        education_level=candidate.education_level,
        skills=[s.skill_name for s in candidate.skills],
        created_at=candidate.created_at,
    )


@router.post("", response_model=CandidateOut, status_code=201)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db)) -> CandidateOut:
    candidate = CandidateService(db).create_candidate(payload)
    return _to_out(candidate)


@router.get("", response_model=list[CandidateOut])
def list_candidates(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CandidateOut]:
    candidates, _total = CandidateService(db).list_candidates(offset=offset, limit=limit)
    return [_to_out(c) for c in candidates]


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)) -> CandidateOut:
    candidate = CandidateService(db).get_candidate(candidate_id)
    return _to_out(candidate)
