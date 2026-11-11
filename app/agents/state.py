"""État partagé qui circule entre les agents du graphe LangGraph."""

from __future__ import annotations

from typing import TypedDict


class PipelineState(TypedDict, total=False):
    # Entrée (jamais de PII directe ici : nom/email/téléphone restent hors
    # du state du graphe, gérés séparément côté API/DB si nécessaire)
    candidate_ref: str
    cv_text: str
    years_experience: int
    skills: list[str]
    required_skills: list[str]

    run_id: str
    correlation_id: str

    # Sorties des agents
    cv_screened: bool
    screening_reason: str
    screening_rules: list[str]
    matched_skills: list[str]
    missing_skills: list[str]

    score: float
    scoring_reason: str
    scoring_rules: list[str]

    interview_notes: str
    interview_notes_by_llm: bool

    onboarding_ready: bool
    onboarding_reason: str
    onboarding_rules: list[str]

    # Traces d'exécution (une entrée par agent exécuté)
    agent_executions: list[dict]
