"""
Glossary OpenMetadata : vocabulaire métier RH.

Crée un glossaire "RH" avec les termes clés du domaine (Candidat, Score de
screening, Décision d'onboarding...) et les rattache aux colonnes des assets
de données (candidate_cv, onboarding_decision) créés dans lineage.py.

Utilité : dans l'UI OpenMetadata, n'importe qui explorant les données voit
la définition métier du champ, pas juste son nom technique.
"""

from __future__ import annotations

from functools import lru_cache

from app.openmetadata.client import get_client, is_enabled
from app.openmetadata.lineage import ensure_cv_and_decision_assets

GLOSSARY_NAME = "RH"

# (nom_du_terme, description) — vocabulaire métier du pipeline RH
GLOSSARY_TERMS = [
    ("Candidat", "Personne ayant postulé à une offre et suivie dans le pipeline RH."),
    (
        "Score de screening",
        "Note sur 100 calculée par l'agent de scoring : 60% expérience, 40% adéquation "
        "des compétences avec le poste.",
    ),
    (
        "Decision onboarding",
        "Décision finale automatisée indiquant si un candidat est prêt à démarrer "
        "le processus d'intégration (seuil : score >= 60).",
    ),
    (
        "Competence requise",
        "Compétence jugée nécessaire pour le poste, utilisée par l'agent de tri de CV "
        "pour filtrer les candidatures.",
    ),
]

# Rattachement terme -> (nom_asset, nom_colonne) pour taguer les bonnes colonnes
TERM_TO_COLUMN = {
    "Candidat": ("candidate_cv", "candidate_id"),
    "Score de screening": ("onboarding_decision", "score"),
    "Decision onboarding": ("onboarding_decision", "onboarding_ready"),
}


@lru_cache(maxsize=1)
def ensure_glossary():
    """Crée (ou récupère) le glossaire RH."""
    from metadata.generated.schema.api.data.createGlossary import CreateGlossaryRequest

    client = get_client()
    request = CreateGlossaryRequest(
        name=GLOSSARY_NAME,
        displayName="Vocabulaire RH",
        description="Termes métier du pipeline de recrutement et d'onboarding.",
    )
    return client.create_or_update(data=request)


@lru_cache(maxsize=1)
def ensure_glossary_terms():
    """Crée (ou récupère) tous les termes du glossaire RH. Retourne un dict name -> term."""
    from metadata.generated.schema.api.data.createGlossaryTerm import CreateGlossaryTermRequest

    client = get_client()
    glossary = ensure_glossary()

    terms = {}
    for name, description in GLOSSARY_TERMS:
        request = CreateGlossaryTermRequest(
            name=name,
            displayName=name,
            description=description,
            glossary=glossary.fullyQualifiedName,
        )
        terms[name] = client.create_or_update(data=request)
    return terms


def tag_columns_with_glossary_terms() -> None:
    """Applique les termes du glossaire aux colonnes correspondantes des assets RH."""
    if not is_enabled():
        return

    try:
        from metadata.generated.schema.type.tagLabel import LabelType, State, TagLabel, TagSource
        from metadata.ingestion.models.table_metadata import ColumnTag

        client = get_client()
        terms = ensure_glossary_terms()
        cv_asset, decision_asset = ensure_cv_and_decision_assets()
        assets_by_name = {"candidate_cv": cv_asset, "onboarding_decision": decision_asset}

        for term_name, (asset_name, column_name) in TERM_TO_COLUMN.items():
            term = terms[term_name]
            table = assets_by_name[asset_name]
            column_fqn = f"{table.fullyQualifiedName.root}.{column_name}"

            tag_label = TagLabel(
                tagFQN=term.fullyQualifiedName.root,
                source=TagSource.Glossary,
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
            "Échec du rattachement des termes de glossaire OpenMetadata : %s", exc
        )
