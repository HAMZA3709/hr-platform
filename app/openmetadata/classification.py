"""
Classification OpenMetadata : tags de sensibilité RGPD sur les données RH.

Crée une classification custom "SensibiliteRH" avec 2 tags (Confidentiel,
Public) et les applique aux colonnes des assets candidate_cv / onboarding_decision,
pour que la sensibilité des données soit visible directement dans le catalogue
(et exploitable ensuite par les policies d'accès OpenMetadata).
"""

from __future__ import annotations

from functools import lru_cache

from app.openmetadata.client import get_client, is_enabled
from app.openmetadata.lineage import ensure_cv_and_decision_assets

CLASSIFICATION_NAME = "SensibiliteRH"

TAGS = [
    ("Confidentiel", "Donnée personnelle identifiante, à traiter selon la politique RGPD."),
    ("Public", "Donnée non identifiante, pas de restriction particulière."),
]

# (nom_asset, nom_colonne) -> nom_du_tag
COLUMN_SENSITIVITY = {
    ("candidate_cv", "candidate_id"): "Confidentiel",
    ("candidate_cv", "years_experience"): "Public",
    ("candidate_cv", "skills"): "Public",
    ("onboarding_decision", "candidate_id"): "Confidentiel",
    ("onboarding_decision", "score"): "Public",
    ("onboarding_decision", "onboarding_ready"): "Public",
}


@lru_cache(maxsize=1)
def ensure_classification():
    """Crée (ou récupère) la classification custom SensibiliteRH."""
    from metadata.generated.schema.api.classification.createClassification import (
        CreateClassificationRequest,
    )

    client = get_client()
    request = CreateClassificationRequest(
        name=CLASSIFICATION_NAME,
        displayName="Sensibilité RH",
        description="Niveau de sensibilité RGPD des données du pipeline RH.",
    )
    return client.create_or_update(data=request)


@lru_cache(maxsize=1)
def ensure_tags():
    """Crée (ou récupère) les tags de sensibilité. Retourne un dict name -> tag."""
    from metadata.generated.schema.api.classification.createTag import CreateTagRequest

    client = get_client()
    classification = ensure_classification()

    tags = {}
    for name, description in TAGS:
        request = CreateTagRequest(
            name=name,
            displayName=name,
            description=description,
            classification=classification.fullyQualifiedName,
        )
        tags[name] = client.create_or_update(data=request)
    return tags


def tag_columns_with_sensitivity() -> None:
    """Applique les tags de sensibilité aux colonnes des assets RH."""
    if not is_enabled():
        return

    try:
        from metadata.generated.schema.type.tagLabel import LabelType, State, TagLabel, TagSource
        from metadata.ingestion.models.table_metadata import ColumnTag

        client = get_client()
        tags = ensure_tags()
        cv_asset, decision_asset = ensure_cv_and_decision_assets()
        assets_by_name = {"candidate_cv": cv_asset, "onboarding_decision": decision_asset}

        for (asset_name, column_name), tag_name in COLUMN_SENSITIVITY.items():
            tag = tags[tag_name]
            table = assets_by_name[asset_name]
            column_fqn = f"{table.fullyQualifiedName.root}.{column_name}"

            tag_label = TagLabel(
                tagFQN=tag.fullyQualifiedName,
                source=TagSource.Classification,
                labelType=LabelType.Manual,
                state=State.Confirmed,
            )
            client.patch_column_tags(
                table=table,
                column_tags=[ColumnTag(column_fqn=column_fqn, tag_label=tag_label)],
            )

    except Exception as exc:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning(
            "Échec du rattachement des tags de sensibilité OpenMetadata : %s", exc
        )
