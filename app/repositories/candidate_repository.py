"""Accès DB pour les candidats — aucune logique métier ici, juste des requêtes."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.pseudonymize import pseudonymize
from app.db.models import Candidate, CandidateSkill


class CandidateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        candidate_ref: str,
        years_experience: int,
        skills: list[str],
        education_level: str | None = None,
        job_offer_id: int | None = None,
    ) -> Candidate:
        candidate = Candidate(
            candidate_ref=candidate_ref,
            pseudonymized_ref=pseudonymize(candidate_ref),
            years_experience=years_experience,
            education_level=education_level,
            job_offer_id=job_offer_id,
        )
        candidate.skills = [CandidateSkill(skill_name=s) for s in skills]
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def get_by_id(self, candidate_id: int) -> Candidate | None:
        return self.db.get(Candidate, candidate_id)

    def get_by_ref(self, candidate_ref: str) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.candidate_ref == candidate_ref)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20) -> tuple[list[Candidate], int]:
        total = self.db.execute(select(Candidate)).scalars().all()
        stmt = select(Candidate).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, len(total)
