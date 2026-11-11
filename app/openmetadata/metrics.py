"""
Metrics OpenMetadata : indicateurs métier calculés à partir du pipeline RH.

Déclare des entités Metric dans OpenMetadata (visibles sous Govern > Metrics)
pour documenter les KPIs métier que votre pipeline calcule, même si le calcul
réel reste fait dans votre code Python (src/agents.py) — l'entité Metric ici
sert à cataloguer/documenter ces indicateurs pour toute l'organisation.
"""

from __future__ import annotations

from functools import lru_cache

from app.openmetadata.client import get_client, is_enabled

# (nom, description, type, formule_en_langage_naturel)
METRICS = [
    (
        "taux_retention_screening",
        "Proportion de candidats dont le CV est retenu après le tri automatique.",
        "PERCENTAGE",
        "nombre de CV retenus / nombre total de CV traités",
    ),
    (
        "score_moyen_candidats",
        "Score moyen attribué par l'agent de scoring sur l'ensemble des candidats traités.",
        "AVERAGE",
        "moyenne(score) sur tous les candidats scorés",
    ),
    (
        "taux_onboarding_pret",
        "Proportion de candidats jugés prêts pour l'onboarding (score >= 60).",
        "PERCENTAGE",
        "nombre de candidats avec onboarding_ready=true / nombre de candidats scorés",
    ),
]


@lru_cache(maxsize=1)
def ensure_metrics() -> dict:
    """Crée (ou récupère) les entités Metric du pipeline RH. Retourne name -> Metric."""
    if not is_enabled():
        return {}

    from metadata.generated.schema.api.data.createMetric import CreateMetricRequest
    from metadata.generated.schema.entity.data.metric import MetricType

    client = get_client()

    metrics = {}
    for name, description, metric_type, formula in METRICS:
        request = CreateMetricRequest(
            name=name,
            displayName=name.replace("_", " ").capitalize(),
            description=f"{description}\n\nFormule : {formula}",
            metricType=MetricType[metric_type],
        )
        metrics[name] = client.create_or_update(data=request)
    return metrics
