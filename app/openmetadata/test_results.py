"""
Pousse de VRAIS résultats de test vers OpenMetadata après chaque run du
pipeline — c'est ce qui peuple les dashboards Observability / Data Health
(Data Assets Coverage, Healthy Data Assets, Test Case Results, Data
Dimensions) au lieu d'afficher des zéros partout.

Contrairement à un "Run Now" manuel dans l'UI (qui exécute une requête SQL
de profiling sur une vraie table), on calcule ici le résultat NOUS-MÊMES à
partir de final_state (puisque nos assets candidate_cv / onboarding_decision
sont des tables "catalogue" sans moteur SQL derrière), puis on le pousse via
add_test_case_results. Un test qui échoue plusieurs fois de suite déclenche
automatiquement un incident dans Incident Manager.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.openmetadata.client import get_client, is_enabled
from app.openmetadata.data_quality import TEST_DEFINITIONS
from app.openmetadata.lineage import ensure_cv_and_decision_assets


def _evaluate_test(test_name: str, column_name: str, params: dict, final_state: dict):
    """Évalue localement si un test passe ou échoue, à partir de final_state.

    Retourne (status: 'Success'|'Failed', result_message: str).
    """
    if test_name == "candidate_id_not_null":
        candidate_id = final_state.get("candidate_id")
        passed = candidate_id is not None and candidate_id != ""
        return ("Success" if passed else "Failed", f"candidate_id = {candidate_id!r}")

    if test_name == "score_in_valid_range":
        score = final_state.get("score")
        if score is None:
            # CV rejeté au tri -> pas de score calculé, le test ne s'applique pas
            return ("Success", "Pas de score calculé (CV non retenu au tri) — test ignoré")
        min_value = float(params.get("minValue", 0))
        max_value = float(params.get("maxValue", 100))
        passed = min_value <= score <= max_value
        return (
            "Success" if passed else "Failed",
            f"score = {score}, attendu entre {min_value} et {max_value}",
        )

    return ("Success", "Test non reconnu localement — ignoré")


def report_test_results(final_state: dict) -> None:
    """Calcule et pousse le résultat de chaque test défini dans data_quality.py."""
    if not is_enabled():
        return

    try:
        from metadata.generated.schema.tests.basic import TestCaseResult, TestCaseStatus

        client = get_client()
        _, decision_asset = ensure_cv_and_decision_assets()
        table_fqn = decision_asset.fullyQualifiedName.root

        now_ms = int(datetime.now(UTC).timestamp() * 1000)

        for test_name, _test_def_fqn, column_name, _description, params in TEST_DEFINITIONS:
            status_str, message = _evaluate_test(test_name, column_name, params, final_state)
            test_case_fqn = f"{table_fqn}.{column_name}.{test_name}"

            result = TestCaseResult(
                timestamp=now_ms,
                testCaseStatus=TestCaseStatus[status_str],
                result=message,
                passedRows=1 if status_str == "Success" else 0,
                failedRows=0 if status_str == "Success" else 1,
            )

            client.add_test_case_results(test_results=result, test_case_fqn=test_case_fqn)

    except Exception as exc:  # noqa: BLE001 - ne jamais casser le pipeline RH
        import logging

        logging.getLogger(__name__).warning(
            "Échec de la remontée des résultats de test OpenMetadata : %s", exc
        )
