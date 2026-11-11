"""Tests unitaires des règles métier (app.core.rules)."""

from __future__ import annotations

from app.core.rules import (
    evaluate_cv_screening,
    evaluate_onboarding_decision,
    evaluate_scoring,
)


def test_screening_passes_with_sufficient_experience_and_skills():
    result = evaluate_cv_screening(
        years_experience=5, skills=["python", "sql"], required_skills=["python", "sql"]
    )
    assert result.passed is True
    assert result.matched_skills == ["python", "sql"]
    assert result.missing_skills == []


def test_screening_fails_with_insufficient_experience():
    result = evaluate_cv_screening(
        years_experience=0, skills=["python", "sql"], required_skills=["python", "sql"]
    )
    assert result.passed is False
    assert "Expérience insuffisante" in result.reason


def test_screening_fails_with_insufficient_skills():
    result = evaluate_cv_screening(
        years_experience=5, skills=["excel"], required_skills=["python", "sql", "leadership"]
    )
    assert result.passed is False
    assert "Compétences insuffisantes" in result.reason


def test_screening_with_no_required_skills_always_passes_skills_component():
    result = evaluate_cv_screening(years_experience=5, skills=[], required_skills=[])
    assert result.passed is True  # ratio=1.0 par convention si aucune compétence requise


def test_scoring_caps_experience_component_at_10_years():
    result_10y = evaluate_scoring(years_experience=10, skills=["python"], required_skills=["python"])
    result_20y = evaluate_scoring(years_experience=20, skills=["python"], required_skills=["python"])
    assert result_10y.experience_component == result_20y.experience_component == 60.0


def test_scoring_full_match_gives_100():
    result = evaluate_scoring(years_experience=10, skills=["python", "sql"], required_skills=["python", "sql"])
    assert result.score == 100.0


def test_scoring_no_match_gives_experience_component_only():
    result = evaluate_scoring(years_experience=10, skills=["cobol"], required_skills=["python", "sql"])
    assert result.score == 60.0


def test_onboarding_ready_above_threshold():
    result = evaluate_onboarding_decision(score=75.0)
    assert result.ready is True


def test_onboarding_not_ready_below_threshold():
    result = evaluate_onboarding_decision(score=10.0)
    assert result.ready is False


def test_onboarding_exactly_at_threshold_is_ready():
    result = evaluate_onboarding_decision(score=60.0)
    assert result.ready is True  # >= , pas >
