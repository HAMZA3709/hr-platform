"""
Intégration OpenMetadata pour le pipeline RH (LangGraph) : Pipeline Service,
Pipeline, Tasks, et statuts d'exécution.

Voir src/openmetadata/client.py pour la configuration de connexion.
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache

from app.openmetadata.client import get_client, is_enabled

PIPELINE_SERVICE_NAME = "hr-agent-pipeline-service"
PIPELINE_NAME = "hr-multi-agent-pipeline"

# Les 4 agents du pipeline -> déclarés comme Tasks OpenMetadata
AGENT_TASKS = [
    ("agent_cv_screening", "Tri de CV"),
    ("agent_scoring", "Scoring du candidat"),
    ("agent_interview_prep", "Préparation entretien"),
    ("agent_onboarding", "Décision onboarding"),
]


@lru_cache(maxsize=1)
def ensure_pipeline_service():
    """Crée (ou récupère) le Pipeline Service custom représentant notre pipeline RH."""
    from metadata.generated.schema.api.services.createPipelineService import (
        CreatePipelineServiceRequest,
    )
    from metadata.generated.schema.entity.services.connections.pipeline.customPipelineConnection import (
        CustomPipelineConnection,
        CustomPipelineType,
    )
    from metadata.generated.schema.entity.services.pipelineService import (
        PipelineConnection,
        PipelineServiceType,
    )

    client = get_client()

    request = CreatePipelineServiceRequest(
        name=PIPELINE_SERVICE_NAME,
        displayName="Pipeline RH — Agents LangGraph",
        serviceType=PipelineServiceType.CustomPipeline,
        connection=PipelineConnection(
            config=CustomPipelineConnection(
                type=CustomPipelineType.CustomPipeline,
                sourcePythonClass="hr_pipeline.CustomSource",
            )
        ),
    )
    return client.create_or_update(data=request)


@lru_cache(maxsize=1)
def ensure_pipeline_entity():
    """Crée (ou récupère) l'entité Pipeline avec un Task par agent."""
    from metadata.generated.schema.api.data.createPipeline import CreatePipelineRequest
    from metadata.generated.schema.entity.data.pipeline import Task

    client = get_client()
    service_entity = ensure_pipeline_service()

    tasks = [
        Task(name=task_name, displayName=display_name, taskType="Agent")
        for task_name, display_name in AGENT_TASKS
    ]

    request = CreatePipelineRequest(
        name=PIPELINE_NAME,
        displayName="Pipeline RH multi-agents",
        description="Tri de CV -> scoring -> préparation entretien -> onboarding",
        service=service_entity.fullyQualifiedName,
        tasks=tasks,
    )
    return client.create_or_update(data=request)


def report_run_to_openmetadata(run_id: str, agent_executions: list[dict]) -> None:
    """Pousse le statut d'un run terminé vers OpenMetadata.

    `agent_executions` : liste de dicts {"agent_name": str, "status": "success"|"error", ...}
    telle que produite par app.services.pipeline_service.

    Silencieux (log un warning) en cas d'erreur, pour ne jamais faire échouer
    le pipeline RH à cause d'un souci de monitoring.
    """
    if not is_enabled():
        return

    try:
        from metadata.generated.schema.entity.data.pipeline import (
            PipelineStatus,
            StatusType,
            TaskStatus,
        )
        from metadata.generated.schema.type.basic import Timestamp

        client = get_client()
        pipeline_entity = ensure_pipeline_entity()

        steps_by_agent = {step["agent_name"]: step for step in agent_executions}
        task_statuses = []
        overall_status = StatusType.Successful

        for task_name, _ in AGENT_TASKS:
            step = steps_by_agent.get(task_name)
            if step is None:
                continue
            status = StatusType.Successful if step["status"] == "success" else StatusType.Failed
            if status == StatusType.Failed:
                overall_status = StatusType.Failed
            task_statuses.append(TaskStatus(name=task_name, executionStatus=status))

        now_ms = int(datetime.now(UTC).timestamp() * 1000)

        pipeline_status = PipelineStatus(
            timestamp=Timestamp(root=now_ms),
            executionStatus=overall_status,
            taskStatus=task_statuses,
        )

        client.add_pipeline_status(
            fqn=pipeline_entity.fullyQualifiedName.root,
            status=pipeline_status,
        )

    except Exception as exc:  # noqa: BLE001 - on ne bloque jamais le pipeline RH
        import logging

        logging.getLogger(__name__).warning(
            "Échec de la remontée OpenMetadata pour run_id=%s : %s", run_id, exc
        )
