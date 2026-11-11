"""Tests du routage conditionnel du graphe et de l'arrêt anticipé."""

from __future__ import annotations

from app.agents.graph import build_graph, route_after_screening


def test_route_after_screening_goes_to_scoring_when_passed():
    assert route_after_screening({"cv_screened": True}) == "agent_scoring"


def test_route_after_screening_ends_when_rejected():
    from langgraph.graph import END

    assert route_after_screening({"cv_screened": False}) == END


def test_full_graph_strong_candidate_reaches_onboarding():
    pipeline = build_graph()
    result = pipeline.invoke(
        {
            "candidate_ref": "cand-strong",
            "cv_text": "",
            "years_experience": 8,
            "skills": ["python", "sql", "leadership"],
            "required_skills": ["python", "sql", "leadership"],
            "run_id": "r1",
            "correlation_id": "c1",
        }
    )
    assert result["cv_screened"] is True
    assert "onboarding_ready" in result
    assert len(result["agent_executions"]) == 4


def test_graph_stops_early_when_screening_rejects():
    pipeline = build_graph()
    result = pipeline.invoke(
        {
            "candidate_ref": "cand-weak",
            "cv_text": "",
            "years_experience": 0,
            "skills": ["excel"],
            "required_skills": ["python", "sql", "leadership"],
            "run_id": "r2",
            "correlation_id": "c2",
        }
    )
    assert result["cv_screened"] is False
    assert "score" not in result
    assert "onboarding_ready" not in result
    assert len(result["agent_executions"]) == 1
