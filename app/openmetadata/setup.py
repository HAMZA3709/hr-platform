"""
Configure TOUTES les fonctionnalités OpenMetadata en une seule commande :
Pipeline Service, Pipeline+Tasks, Lineage, Glossaire RH, Classification RGPD,
Data Quality (Test Suite + Test Cases), Metrics métier.

Usage :
    python -m app.openmetadata.setup

Ne fait rien si OPENMETADATA_ENABLED n'est pas à true dans .env. N'effectue
aucune opération destructive : uniquement des create_or_update (idempotent).
"""

from __future__ import annotations

from app.openmetadata.classification import (
    ensure_classification,
    ensure_tags,
    tag_columns_with_sensitivity,
)
from app.openmetadata.client import is_enabled
from app.openmetadata.data_quality import setup_data_quality
from app.openmetadata.glossary import (
    ensure_glossary,
    ensure_glossary_terms,
    tag_columns_with_glossary_terms,
)
from app.openmetadata.lineage import ensure_cv_and_decision_assets, report_lineage
from app.openmetadata.metrics import ensure_metrics
from app.openmetadata.pipeline_service import ensure_pipeline_entity, ensure_pipeline_service


def run_full_setup() -> dict:
    """Exécute toutes les étapes et retourne un résumé {étape: 'ok'|'skipped'}."""
    if not is_enabled():
        return {"status": "skipped", "reason": "OPENMETADATA_ENABLED n'est pas à true"}

    summary = {}

    ensure_pipeline_service()
    ensure_pipeline_entity()
    summary["pipeline"] = "ok"

    ensure_cv_and_decision_assets()
    summary["data_assets"] = "ok"

    report_lineage()
    summary["lineage"] = "ok"

    ensure_glossary()
    ensure_glossary_terms()
    tag_columns_with_glossary_terms()
    summary["glossary"] = "ok"

    ensure_classification()
    ensure_tags()
    tag_columns_with_sensitivity()
    summary["classification"] = "ok"

    setup_data_quality()
    summary["data_quality"] = "ok"

    ensure_metrics()
    summary["metrics"] = "ok"

    return {"status": "done", "steps": summary}


if __name__ == "__main__":
    result = run_full_setup()
    print(result)
