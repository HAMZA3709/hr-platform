"""Service candidats : logique métier, séparée des routes FastAPI."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationAppError
from app.db.models import Candidate
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate import CandidateCreate


class CandidateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CandidateRepository(db)

    def create_candidate(self, payload: CandidateCreate) -> Candidate:
        existing = self.repo.get_by_ref(payload.candidate_ref)
        if existing is not None:
            raise ValidationAppError(
                f"Un candidat avec candidate_ref='{payload.candidate_ref}' existe déjà."
            )
        return self.repo.create(
            candidate_ref=payload.candidate_ref,
            years_experience=payload.years_experience,
            skills=payload.skills,
            education_level=payload.education_level,
            job_offer_id=payload.job_offer_id,
        )

    def get_candidate(self, candidate_id: int) -> Candidate:
        candidate = self.repo.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError(f"Candidat {candidate_id} introuvable.")
        return candidate

    def list_candidates(self, offset: int, limit: int) -> tuple[list[Candidate], int]:
        return self.repo.list(offset=offset, limit=limit)
