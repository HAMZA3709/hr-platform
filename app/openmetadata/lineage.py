"""
Lineage OpenMetadata : CV (entrée) -> Pipeline RH -> Décision onboarding (sortie).

Modélise les deux extrémités du flux comme des entités "Table" légères,
rattachées à un Database Service custom (pattern standard OpenMetadata pour
cataloguer des assets de données génériques sans base SQL réelle derrière).
"""

from __future__ import annotations

from functools import lru_cache

from app.openmetadata.client import get_client, is_enabled
from app.openmetadata.pipeline_service import ensure_pipeline_entity

DATA_SERVICE_NAME = "hr-agent-data-service"
CV_ASSET_NAME = "candidate_cv"
DECISION_ASSET_NAME = "onboarding_decision"

DATABASE_NAME = "hr_pipeline_data"
SCHEMA_NAME = "candidates"


@lru_cache(maxsize=1)
def ensure_data_service():
    """Crée (ou récupère) le Database Service custom qui porte nos assets."""
    from metadata.generated.schema.api.services.createDatabaseService import (
        CreateDatabaseServiceRequest,
    )
    from metadata.generated.schema.entity.services.connections.database.customDatabaseConnection import (
        CustomDatabaseConnection,
        CustomDatabaseType,
    )
    from metadata.generated.schema.entity.services.databaseService import (
        DatabaseConnection,
        DatabaseServiceType,
    )

    client = get_client()

    request = CreateDatabaseServiceRequest(
        name=DATA_SERVICE_NAME,
        displayName="Données RH — Pipeline agents",
        serviceType=DatabaseServiceType.CustomDatabase,
        connection=DatabaseConnection(
            config=CustomDatabaseConnection(
                type=CustomDatabaseType.CustomDatabase,
                sourcePythonClass="hr_pipeline.CustomSource",
            )
        ),
    )
    return client.create_or_update(data=request)


@lru_cache(maxsize=1)
def ensure_database_and_schema():
    """Crée (ou récupère) une Database + un Schema conteneurs pour nos assets."""
    from metadata.generated.schema.api.data.createDatabase import CreateDatabaseRequest
    from metadata.generated.schema.api.data.createDatabaseSchema import (
        CreateDatabaseSchemaRequest,
    )

    client = get_client()
    service_entity = ensure_data_service()

    database = client.create_or_update(
        data=CreateDatabaseRequest(name=DATABASE_NAME, service=service_entity.fullyQualifiedName)
    )
    schema = client.create_or_update(
        data=CreateDatabaseSchemaRequest(name=SCHEMA_NAME, database=database.fullyQualifiedName)
    )
    return database, schema


@lru_cache(maxsize=8)
def ensure_asset(name: str, display_name: str, columns: tuple[tuple[str, str], ...]):
    """Crée (ou récupère) un asset 'Table' représentant une entrée/sortie de données.

    columns: tuple de (nom_colonne, type_openmetadata), ex: (("candidate_id", "STRING"),)
    Pour une colonne de type ARRAY, le type des éléments est déduit en STRING
    par défaut (OpenMetadata exige arrayDataType pour tout type ARRAY).
    """
    from metadata.generated.schema.api.data.createTable import CreateTableRequest
    from metadata.generated.schema.entity.data.table import Column, DataType

    client = get_client()
    _, schema_entity = ensure_database_and_schema()

    table_columns = []
    for col_name, col_type in columns:
        data_type = DataType[col_type]
        column_kwargs = {"name": col_name, "dataType": data_type}
        if data_type == DataType.ARRAY:
            column_kwargs["arrayDataType"] = DataType.STRING
        table_columns.append(Column(**column_kwargs))

    request = CreateTableRequest(
        name=name,
        displayName=display_name,
        databaseSchema=schema_entity.fullyQualifiedName,
        columns=table_columns,
    )
    return client.create_or_update(data=request)


def ensure_cv_and_decision_assets():
    """Crée les 2 assets de données (CV en entrée, décision en sortie)."""
    cv_asset = ensure_asset(
        CV_ASSET_NAME,
        "CV candidat",
        (
            ("candidate_id", "STRING"),
            ("years_experience", "INT"),
            ("skills", "ARRAY"),
        ),
    )
    decision_asset = ensure_asset(
        DECISION_ASSET_NAME,
        "Décision onboarding",
        (
            ("candidate_id", "STRING"),
            ("score", "FLOAT"),
            ("onboarding_ready", "BOOLEAN"),
        ),
    )
    return cv_asset, decision_asset


def report_lineage() -> None:
    """Déclare le lineage CV -> Pipeline RH -> Décision onboarding.

    Relation statique, à appeler une fois (ex: au démarrage de l'app).
    """
    if not is_enabled():
        return

    try:
        from metadata.generated.schema.api.lineage.addLineage import AddLineageRequest
        from metadata.generated.schema.type.entityLineage import EntitiesEdge, LineageDetails
        from metadata.generated.schema.type.entityReference import EntityReference

        client = get_client()
        cv_asset, decision_asset = ensure_cv_and_decision_assets()
        pipeline_entity = ensure_pipeline_entity()

        def _ref(entity, entity_type: str) -> EntityReference:
            return EntityReference(id=entity.id, type=entity_type)

        client.add_lineage(
            data=AddLineageRequest(
                edge=EntitiesEdge(
                    fromEntity=_ref(cv_asset, "table"),
                    toEntity=_ref(pipeline_entity, "pipeline"),
                    lineageDetails=LineageDetails(
                        pipeline=_ref(pipeline_entity, "pipeline"),
                        description="Le pipeline RH lit le CV du candidat en entrée",
                    ),
                )
            )
        )

        client.add_lineage(
            data=AddLineageRequest(
                edge=EntitiesEdge(
                    fromEntity=_ref(pipeline_entity, "pipeline"),
                    toEntity=_ref(decision_asset, "table"),
                    lineageDetails=LineageDetails(
                        pipeline=_ref(pipeline_entity, "pipeline"),
                        description="Le pipeline RH produit la décision d'onboarding",
                    ),
                )
            )
        )

    except Exception as exc:  # noqa: BLE001 - ne jamais casser le pipeline RH
        import logging

        logging.getLogger(__name__).warning("Échec de la remontée du lineage OpenMetadata : %s", exc)
