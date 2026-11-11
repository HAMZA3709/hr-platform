"""Agent 4 : décision d'onboarding — déterministe (app.core.rules)."""

from __future__ import annotations

import time

from app.agents.state import PipelineState
from app.core.rules import evaluate_onboarding_decision
from app.llm.service import generate


def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()

    result = evaluate_onboarding_decision(score=state["score"])

    llm_result = generate(
        system=(
            "Tu es un agent RH. Rédige une phrase brève confirmant la décision "
            "d'onboarding déjà prise (ne prends pas de décision toi-même)."
        ),
        prompt=f"Décision déjà prise : {'prêt' if result.ready else 'non prêt'}.\nRaison : {result.reason}",
    )

    duration_ms = (time.perf_counter() - t0) * 1000
    executions = list(state.get("agent_executions", []))
    executions.append(
        {
            "agent_name": "agent_onboarding",
            "status": "success",
            "duration_ms": round(duration_ms, 2),
            "tokens_in": llm_result.tokens_in,
            "tokens_out": llm_result.tokens_out,
            "llm_provider": llm_result.provider,
        }
    )

    return {
        **state,
        "onboarding_ready": result.ready,
        "onboarding_reason": result.reason,
        "onboarding_rules": result.rules_applied,
        "agent_executions": executions,
    }
