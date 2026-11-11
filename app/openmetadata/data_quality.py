"""
Data Quality OpenMetadata : tests automatisés sur les données RH.

Crée une Test Suite rattachée à l'asset `onboarding_decision` avec des tests
sur les colonnes (valeurs non nulles, score dans une plage valide).

Ces tests utilisent les DÉFINITIONS DE TEST INTÉGRÉES d'OpenMetadata
(columnValuesToBeNotNull, columnValuesToBeBetween) qui existent par défaut
sur toute instance standard. Si votre instance a été fortement personnalisée
et que ces noms ne correspondent à rien, vérifiez les noms exacts dans
Governance > Test Definitions (ou Data Quality > Test Library) dans l'UI et
ajustez TEST_DEFINITIONS ci-dessous.

Une fois les tests créés, exécutez-les (manuellement dans l'UI via
"Run Now", ou automatiquement si vous avez un workflow d'ingestion de
profiling programmé) pour que des résultats apparaissent. Un test qui
échoue plusieurs fois de suite déclenche automatiquement un incident dans
Observability > Incident Manager — aucun code supplémentaire n'est requis
pour ça, c'est un comportement natif d'OpenMetadata une fois les tests en
place. Les Alertes (Settings > Alerts) sont à configurer dans l'UI pour être
notifié (email/Slack/Teams) quand un incident est ouvert.
"""

from __future__ import annotations

from functools import lru_cache

from app.openmetadata.client import get_client, is_enabled
from app.openmetadata.lineage import ensure_cv_and_decision_assets

TEST_SUITE_NAME = "hr_onboarding_decision_quality"

# (nom_test_case, test_definition_fqn, colonne_ciblee, description, params)
TEST_DEFINITIONS = [
    (
        "candidate_id_not_null",
        "columnValuesToBeNotNull",
        "candidate_id",
        "L'identifiant candidat ne doit jamais être vide.",
        {},
    ),
    (
        "score_in_valid_range",
        "columnValuesToBeBetween",
        "score",
        "Le score de screening doit toujours être compris entre 0 et 100.",
        {"minValue": "0", "maxValue": "100"},
    ),
]


@lru_cache(maxsize=1)
def ensure_test_suite():
    """Crée (ou récupère) la Test Suite rattachée à l'asset onboarding_decision."""
    client = get_client()
    _, decision_asset = ensure_cv_and_decision_assets()

    # get_or_create_executable_test_suite lie directement la suite à la table cible
    return client.get_or_create_executable_test_suite(
        entity_fqn=decision_asset.fullyQualifiedName.root,
    )


def ensure_test_cases() -> list:
    """Crée (ou récupère) les tests de qualité de données définis dans TEST_DEFINITIONS."""
    if not is_enabled():
        return []

    try:
        from metadata.generated.schema.tests.testCase import TestCaseParameterValue

        client = get_client()
        _, decision_asset = ensure_cv_and_decision_assets()
        table_fqn = decision_asset.fullyQualifiedName.root

        created = []
        for test_name, test_def_fqn, column_name, description, params in TEST_DEFINITIONS:
            # Vérifie/récupère la définition de test intégrée (ne la recrée pas si déjà existante)
            client.get_or_create_test_definition(test_definition_fqn=test_def_fqn)

            entity_link = (
                f"<#E::table::{table_fqn}::columns::{column_name}>"
                if column_name
                else f"<#E::table::{table_fqn}>"
            )

            param_values = [
                TestCaseParameterValue(name=k, value=v) for k, v in params.items()
            ] or None

            test_case = client.get_or_create_test_case(
                test_case_fqn=f"{table_fqn}.{column_name}.{test_name}",
                entity_link=entity_link,
                test_definition_fqn=test_def_fqn,
                test_case_parameter_values=param_values,
                description=description,
            )
            created.append(test_case)

        return created

    except Exception as exc:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning(
            "Échec de la création des tests de qualité OpenMetadata : %s", exc
        )
        return []


def setup_data_quality() -> None:
    """Point d'entrée : crée la Test Suite + tous les Test Cases."""
    if not is_enabled():
        return
    ensure_test_suite()
    ensure_test_cases()
