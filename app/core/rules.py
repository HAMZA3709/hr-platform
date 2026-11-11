"""
Règles métier du pipeline RH — toutes déterministes et testables.

Le LLM ne décide jamais : il ne fait que produire du texte explicatif. Ce
module contient la seule logique qui détermine retenu/rejeté, le score, et
prêt/non-prêt pour l'onboarding.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass
class ScreeningResult:
    passed: bool
    matched_skills: list[str]
    missing_skills: list[str]
    reason: str
    rules_applied: list[str]
    fields_used: list[str]


@dataclass
class ScoringResult:
    score: float
    experience_component: float
    skills_component: float
    reason: str
    rules_applied: list[str]
    fields_used: list[str]


@dataclass
class OnboardingDecisionResult:
    ready: bool
    reason: str
    rules_applied: list[str]
    fields_used: list[str]


def evaluate_cv_screening(
    years_experience: int, skills: list[str], required_skills: list[str]
) -> ScreeningResult:
    """Décide si un CV est retenu, selon des règles configurables (settings)."""
    settings = get_settings()

    matched = sorted(set(skills) & set(required_skills))
    missing = sorted(set(required_skills) - set(skills))

    ratio = len(matched) / len(required_skills) if required_skills else 1.0
    experience_ok = years_experience >= settings.min_years_experience
    skills_ok = ratio >= settings.min_required_skills_matched_ratio

    passed = experience_ok and skills_ok

    rules_applied = [
        f"min_years_experience={settings.min_years_experience}",
        f"min_required_skills_matched_ratio={settings.min_required_skills_matched_ratio}",
    ]

    if not experience_ok:
        reason = (
            f"Expérience insuffisante ({years_experience} ans, "
            f"minimum {settings.min_years_experience})."
        )
    elif not skills_ok:
        reason = (
            f"Compétences insuffisantes ({len(matched)}/{len(required_skills)} requises, "
            f"minimum {settings.min_required_skills_matched_ratio:.0%})."
        )
    else:
        reason = f"{len(matched)}/{len(required_skills)} compétences requises trouvées."

    return ScreeningResult(
        passed=passed,
        matched_skills=matched,
        missing_skills=missing,
        reason=reason,
        rules_applied=rules_applied,
        fields_used=["years_experience", "skills", "required_skills"],
    )


def evaluate_scoring(
    years_experience: int, skills: list[str], required_skills: list[str]
) -> ScoringResult:
    """Calcule un score sur 100 : 60% expérience (plafonnée à 10 ans), 40% compétences."""
    experience_component = min(years_experience / 10, 1.0) * 60
    ratio = (
        len(set(skills) & set(required_skills)) / len(required_skills) if required_skills else 1.0
    )
    skills_component = ratio * 40
    score = round(experience_component + skills_component, 1)

    return ScoringResult(
        score=score,
        experience_component=round(experience_component, 1),
        skills_component=round(skills_component, 1),
        reason="score = 60% expérience (plafond 10 ans) + 40% adéquation compétences",
        rules_applied=["experience_weight=0.6", "skills_weight=0.4", "experience_cap_years=10"],
        fields_used=["years_experience", "skills", "required_skills"],
    )


def evaluate_onboarding_decision(score: float) -> OnboardingDecisionResult:
    """Décide si le candidat est prêt pour l'onboarding, selon un seuil configurable."""
    settings = get_settings()
    ready = score >= settings.min_score_for_onboarding

    return OnboardingDecisionResult(
        ready=ready,
        reason=f"seuil onboarding = {settings.min_score_for_onboarding}, score = {score}",
        rules_applied=[f"min_score_for_onboarding={settings.min_score_for_onboarding}"],
        fields_used=["score"],
    )
