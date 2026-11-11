"""
Service pipeline : exécute le graphe LangGraph pour un candidat, et
coordonne la persistance (repositories), l'audit RGPD, les métriques
Prometheus, et la remontée vers OpenMetadata.

C'est le seul endroit où toutes ces briques se rencontrent — les agents
eux-mêmes (app/agents/*) n'ont aucune dépendance DB/monitoring directe.
"""

from __future__ import annotations

import time
import uuid

from sqlalchemy.orm import Session

from app.agents.graph import build_graph
from app.audit.logger import log_and_persist_decision
from app.core.errors import NotFoundError
from app.db.models import Candidate, PipelineRun
from app.monitoring.metrics import record_agent_execution, record_pipeline_run
from app.openmetadata.pipeline_service import report_run_to_openmetadata
from app.openmetadata.test_results import report_test_results
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.pipeline_repository import PipelineRunRepository

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_graph()
    return _pipeline


class PipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.candidate_repo = CandidateRepository(db)
        self.run_repo = PipelineRunRepository(db)

    def run_pipeline_for_candidate(self, candidate_id: int, correlation_id: str) -> PipelineRun:
        candidate = self.candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError(f"Candidat {candidate_id} introuvable.")

        run_id = str(uuid.uuid4())
        run = self.run_repo.create(run_id=run_id, candidate_id=candidate.id, correlation_id=correlation_id)

        skills = [s.skill_name for s in candidate.skills]
        required_skills = (
            candidate.job_offer.required_skills if candidate.job_offer is not None else skills
        )

        initial_state = {
            "candidate_ref": candidate.candidate_ref,
            "cv_text": "",  # le texte de CV brut n'est volontairement pas repersisté ici
            "years_experience": candidate.years_experience,
            "skills": skills,
            "required_skills": required_skills,
            "run_id": run_id,
            "correlation_id": correlation_id,
        }

        t0 = time.perf_counter()
        status = "success"
        try:
            final_state = _get_pipeline().invoke(initial_state)
        except Exception:
            status = "error"
            duration_s = time.perf_counter() - t0
            record_pipeline_run(status="error", duration_s=duration_s)
            self.run_repo.finalize(run, status="error", duration_ms=duration_s * 1000)
            raise
        duration_s = time.perf_counter() - t0

        if not final_state.get("cv_screened"):
            status = "rejected_at_screening"

        self._persist_agent_executions(run, final_state)
        self._persist_results(run, final_state)
        self._audit(candidate, run, final_state)

        # OpenMetadata : ne doit jamais faire échouer le pipeline RH (fonctions
        # internes déjà no-op si OPENMETADATA_ENABLED=false, et défensives sinon).
        report_run_to_openmetadata(run_id, final_state.get("agent_executions", []))
        report_test_results({**final_state, "candidate_id": final_state.get("candidate_ref")})

        record_pipeline_run(status=status, duration_s=duration_s)
        self.run_repo.finalize(run, status=status, duration_ms=duration_s * 1000)

        return run

    def _persist_agent_executions(self, run: PipelineRun, final_state: dict) -> None:
        for execution in final_state.get("agent_executions", []):
            self.run_repo.add_agent_execution(
                run,
                agent_name=execution["agent_name"],
                status=execution["status"],
                duration_ms=execution["duration_ms"],
                tokens_in=execution["tokens_in"],
                tokens_out=execution["tokens_out"],
                llm_provider=execution["llm_provider"],
            )
            record_agent_execution(
                agent_name=execution["agent_name"],
                status=execution["status"],
                duration_s=execution["duration_ms"] / 1000,
                tokens_in=execution["tokens_in"],
                tokens_out=execution["tokens_out"],
                llm_provider=execution["llm_provider"],
            )

    def _persist_results(self, run: PipelineRun, final_state: dict) -> None:
        self.run_repo.save_screening_result(
            run,
            passed=final_state["cv_screened"],
            matched_skills=final_state.get("matched_skills", []),
            missing_skills=final_state.get("missing_skills", []),
            reason=final_state.get("screening_reason", ""),
            rules_applied=final_state.get("screening_rules", []),
        )

        if "score" not in final_state:
            return  # arrêt anticipé : pas de scoring/entretien/onboarding

        self.run_repo.save_scoring_result(
            run,
            score=final_state["score"],
            experience_component=0.0,
            skills_component=0.0,
            reason=final_state.get("scoring_reason", ""),
            rules_applied=final_state.get("scoring_rules", []),
        )
        self.run_repo.save_interview_preparation(
            run,
            notes=final_state.get("interview_notes", ""),
            generated_by_llm=final_state.get("interview_notes_by_llm", False),
        )
        self.run_repo.save_onboarding_decision(
            run,
            ready=final_state.get("onboarding_ready", False),
            reason=final_state.get("onboarding_reason", ""),
            rules_applied=final_state.get("onboarding_rules", []),
        )

    def _audit(self, candidate: Candidate, run: PipelineRun, final_state: dict) -> None:
        log_and_persist_decision(
            self.db,
            candidate_ref=candidate.candidate_ref,
            action="cv_screening",
            agent="agent_cv_screening",
            decision="retenu" if final_state["cv_screened"] else "rejete",
            justification=final_state.get("screening_reason"),
            rules_applied=final_state.get("screening_rules", []),
            fields_used=["years_experience", "skills", "required_skills"],
            correlation_id=run.correlation_id,
            run_id=run.run_id,
        )
        if "onboarding_ready" in final_state:
            log_and_persist_decision(
                self.db,
                candidate_ref=candidate.candidate_ref,
                action="onboarding_decision",
                agent="agent_onboarding",
                decision="pret" if final_state["onboarding_ready"] else "non_pret",
                justification=final_state.get("onboarding_reason"),
                rules_applied=final_state.get("onboarding_rules", []),
                fields_used=["score"],
                correlation_id=run.correlation_id,
                run_id=run.run_id,
            )
