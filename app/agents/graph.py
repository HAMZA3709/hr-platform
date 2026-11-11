"""
Assemblage du pipeline RH en graphe LangGraph.

Flux : tri CV -> (si retenu) scoring -> prép. entretien -> décision onboarding
Arrêt immédiat si le CV est rejeté au tri.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents import cv_screening, interview_prep, onboarding, scoring
from app.agents.state import PipelineState


def route_after_screening(state: PipelineState) -> str:
    return "agent_scoring" if state.get("cv_screened") else END


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("agent_cv_screening", cv_screening.run)
    graph.add_node("agent_scoring", scoring.run)
    graph.add_node("agent_interview_prep", interview_prep.run)
    graph.add_node("agent_onboarding", onboarding.run)

    graph.set_entry_point("agent_cv_screening")
    graph.add_conditional_edges(
        "agent_cv_screening",
        route_after_screening,
        {"agent_scoring": "agent_scoring", END: END},
    )
    graph.add_edge("agent_scoring", "agent_interview_prep")
    graph.add_edge("agent_interview_prep", "agent_onboarding")
    graph.add_edge("agent_onboarding", END)

    return graph.compile()
