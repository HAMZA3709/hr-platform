"""
Script de données de démonstration : crée une offre d'emploi, quelques
candidats, et lance le pipeline pour chacun.

Usage:
    python -m scripts.seed_demo_data
"""

from __future__ import annotations

from app.db.models import JobOffer
from app.db.session import SessionLocal, init_db
from app.schemas.candidate import CandidateCreate
from app.services.candidate_service import CandidateService
from app.services.pipeline_service import PipelineService

REQUIRED_SKILLS = ["python", "sql", "leadership"]

DEMO_CANDIDATES = [
    {"candidate_ref": "demo-001", "years_experience": 6, "skills": ["python", "sql", "leadership"]},
    {"candidate_ref": "demo-002", "years_experience": 1, "skills": ["excel"]},
    {"candidate_ref": "demo-003", "years_experience": 9, "skills": ["python", "sql", "leadership", "docker"]},
    {"candidate_ref": "demo-004", "years_experience": 3, "skills": ["java", "sql"]},
]


def _get_or_create_demo_job_offer(db) -> JobOffer:
    existing = db.query(JobOffer).filter_by(title="Ingénieur logiciel senior (démo)").first()
    if existing is not None:
        return existing
    job_offer = JobOffer(
        title="Ingénieur logiciel senior (démo)",
        required_skills=REQUIRED_SKILLS,
        min_years_experience=2,
    )
    db.add(job_offer)
    db.commit()
    db.refresh(job_offer)
    return job_offer


def main() -> None:
    init_db()
    db = SessionLocal()
    job_offer = _get_or_create_demo_job_offer(db)

    candidate_service = CandidateService(db)
    pipeline_service = PipelineService(db)

    for data in DEMO_CANDIDATES:
        existing = candidate_service.repo.get_by_ref(data["candidate_ref"])
        if existing is not None:
            print(f"{data['candidate_ref']} existe déjà, on passe.")
            continue

        candidate = candidate_service.create_candidate(
            CandidateCreate(job_offer_id=job_offer.id, **data)
        )
        run = pipeline_service.run_pipeline_for_candidate(candidate.id, correlation_id="seed-script")
        print(f"{data['candidate_ref']} -> run {run.run_id} ({run.status})")

    db.close()


if __name__ == "__main__":
    main()

