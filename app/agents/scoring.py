"""Agent 2 : scoring du candidat — calcul déterministe (app.core.rules)."""

from __future__ import annotations

import time

from app.agents.state import PipelineState
from app.core.rules import evaluate_scoring
from app.llm.service import generate


def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()

    result = evaluate_scoring(
        years_experience=state["years_experience"],
        skills=state["skills"],
        required_skills=state["required_skills"],
    )

    llm_result = generate(
        system=(
            "Tu es un agent RH de scoring. Rédige une phrase brève expliquant "
            "le score déjà calculé (ne recalcule rien, ne change pas le score)."
        ),
        prompt=(
            f"Score calculé : {result.score}/100 "
            f"(expérience: {result.experience_component}, compétences: {result.skills_component}).\n"
            f"Raison technique : {result.reason}"
        ),
    )

    duration_ms = (time.perf_counter() - t0) * 1000
    executions = list(state.get("agent_executions", []))
    executions.append(
        {
            "agent_name": "agent_scoring",
            "status": "success",
            "duration_ms": round(duration_ms, 2),
            "tokens_in": llm_result.tokens_in,
            "tokens_out": llm_result.tokens_out,
            "llm_provider": llm_result.provider,
        }
    )

    return {
        **state,
        "score": result.score,
        "scoring_reason": result.reason,
        "scoring_rules": result.rules_applied,
        "agent_executions": executions,
    }
