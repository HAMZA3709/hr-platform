"""Agent 3 : préparation d'entretien — notes en langage naturel (LLM ou simulation)."""

from __future__ import annotations

import time

from app.agents.state import PipelineState
from app.llm.service import generate


def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()

    missing = state.get("missing_skills", [])
    llm_result = generate(
        system=(
            "Tu es un agent RH qui prépare des notes d'entretien à destination "
            "de l'équipe RH, en français, factuelles et concises (3-4 phrases max)."
        ),
        prompt=(
            f"Score du candidat : {state['score']}/100.\n"
            f"Compétences manquantes à explorer en entretien : "
            f"{', '.join(missing) if missing else 'aucune'}.\n"
            "Rédige des notes de préparation d'entretien pour le recruteur."
        ),
    )

    notes = llm_result.text if llm_result.provider != "simulation" else (
        f"Score global: {state['score']}/100. "
        f"Points à approfondir en entretien: {', '.join(missing) if missing else 'aucun'}."
    )

    duration_ms = (time.perf_counter() - t0) * 1000
    executions = list(state.get("agent_executions", []))
    executions.append(
        {
            "agent_name": "agent_interview_prep",
            "status": "success",
            "duration_ms": round(duration_ms, 2),
            "tokens_in": llm_result.tokens_in,
            "tokens_out": llm_result.tokens_out,
            "llm_provider": llm_result.provider,
        }
    )

    return {
        **state,
        "interview_notes": notes,
        "interview_notes_by_llm": llm_result.provider != "simulation",
        "agent_executions": executions,
    }
