"""
Connexion centrale à OpenMetadata, partagée par tous les modules
(pipeline_service, lineage, glossary, classification, data_quality, metrics).

Config via app.core.config.Settings (OPENMETADATA_ENABLED, OPENMETADATA_HOST_PORT,
OPENMETADATA_JWT_TOKEN dans .env).

Une indisponibilité d'OpenMetadata ne doit JAMAIS empêcher le pipeline RH de
fonctionner — chaque fonction publique de ce package attrape ses propres
erreurs et logue un warning plutôt que de lever une exception, sauf
`get_client()` lui-même et les health checks explicites.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings


def is_enabled() -> bool:
    return get_settings().openmetadata_enabled


@lru_cache(maxsize=1)
def get_client():
    """Crée (une seule fois) le client OpenMetadata authentifié par JWT."""
    from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
        OpenMetadataConnection,
    )
    from metadata.generated.schema.security.client.openMetadataJWTClientConfig import (
        OpenMetadataJWTClientConfig,
    )
    from metadata.ingestion.ometa.ometa_api import OpenMetadata

    settings = get_settings()
    server_config = OpenMetadataConnection(
        hostPort=settings.openmetadata_host_port,
        authProvider="openmetadata",
        securityConfig=OpenMetadataJWTClientConfig(jwtToken=settings.openmetadata_jwt_token or ""),
    )
    client = OpenMetadata(server_config)
    if not client.health_check():
        raise ConnectionError(
            "Impossible de joindre le serveur OpenMetadata. "
            "Vérifiez OPENMETADATA_HOST_PORT et OPENMETADATA_JWT_TOKEN dans .env."
        )
    return client
