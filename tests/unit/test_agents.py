"""Tests unitaires des 4 agents LangGraph (app.agents.*)."""

from __future__ import annotations

from app.agents import cv_screening, interview_prep, onboarding, scoring


def _base_state(**overrides):
    state = {
        "candidate_ref": "cand-test",
        "cv_text": "CV de test",
        "years_experience": 5,
        "skills": ["python", "sql"],
        "required_skills": ["python", "sql"],
        "run_id": "run-test",
        "correlation_id": "corr-test",
        "agent_executions": [],
    }
    state.update(overrides)
    return state


def test_agent_cv_screening_records_execution_trace():
    state = cv_screening.run(_base_state())
    assert state["cv_screened"] is True
    assert len(state["agent_executions"]) == 1
    assert state["agent_executions"][0]["agent_name"] == "agent_cv_screening"


def test_agent_scoring_computes_score():
    # years_experience=5 (50% du plafond de 10 ans) + 100% compétences requises
    # -> score = 5/10*60 + 1.0*40 = 30 + 40 = 70.0
    state = scoring.run(_base_state())
    assert state["score"] == 70.0
    assert len(state["agent_executions"]) == 1


def test_agent_interview_prep_generates_notes():
    state = interview_prep.run(_base_state(score=88.0, missing_skills=["leadership"]))
    assert "88.0" in state["interview_notes"]
    assert "leadership" in state["interview_notes"]


def test_agent_onboarding_ready_above_threshold():
    state = onboarding.run(_base_state(score=75.0))
    assert state["onboarding_ready"] is True


def test_agent_onboarding_not_ready_below_threshold():
    state = onboarding.run(_base_state(score=10.0))
    assert state["onboarding_ready"] is False


def test_agent_executions_accumulate_across_calls():
    state = _base_state()
    state = cv_screening.run(state)
    state = scoring.run(state)
    assert len(state["agent_executions"]) == 2
    assert [e["agent_name"] for e in state["agent_executions"]] == [
        "agent_cv_screening",
        "agent_scoring",
    ]
