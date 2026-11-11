"""
Test d'intégration OpenMetadata — entièrement mocké : aucune vraie instance
OpenMetadata n'est requise ni modifiée. Vérifie que :
  - is_enabled() respecte la config
  - une indisponibilité du client ne fait jamais planter l'appelant
    (comportement attendu : log un warning, ne lève rien)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.openmetadata.client import is_enabled
from app.openmetadata.pipeline_service import report_run_to_openmetadata


def test_is_enabled_reflects_settings(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("OPENMETADATA_ENABLED", "false")
    get_settings.cache_clear()
    assert is_enabled() is False

    monkeypatch.setenv("OPENMETADATA_ENABLED", "true")
    get_settings.cache_clear()
    assert is_enabled() is True

    monkeypatch.setenv("OPENMETADATA_ENABLED", "false")
    get_settings.cache_clear()


def test_report_run_does_nothing_when_disabled(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("OPENMETADATA_ENABLED", "false")
    get_settings.cache_clear()

    class FakeRunContext:
        run_id = "run-om-test"
        steps = []

    # Ne doit lever aucune exception, même sans configuration OpenMetadata
    report_run_to_openmetadata(FakeRunContext(), {})


def test_report_run_never_raises_when_client_unavailable(monkeypatch):
    """Même activé, une erreur de connexion OpenMetadata ne doit JAMAIS
    remonter jusqu'à l'appelant (le pipeline RH doit continuer de fonctionner)."""
    from app.core.config import get_settings

    monkeypatch.setenv("OPENMETADATA_ENABLED", "true")
    monkeypatch.setenv("OPENMETADATA_HOST_PORT", "http://fake-host-for-test:8585/api")
    monkeypatch.setenv("OPENMETADATA_JWT_TOKEN", "fake-token")
    get_settings.cache_clear()

    class FakeRunContext:
        run_id = "run-om-test-2"
        steps = [{"agent": "agent_cv_screening", "status": "success"}]

    with patch("app.openmetadata.pipeline_service.get_client") as mock_get_client:
        mock_get_client.side_effect = ConnectionError("Serveur OpenMetadata injoignable (simulé)")

        # Ne doit pas lever malgré l'échec de connexion simulé
        report_run_to_openmetadata(FakeRunContext(), {})

    monkeypatch.setenv("OPENMETADATA_ENABLED", "false")
    get_settings.cache_clear()


def test_ensure_pipeline_service_called_with_mocked_client(monkeypatch):
    """Vérifie que ensure_pipeline_service construit bien la requête attendue,
    sans jamais contacter un vrai serveur (client entièrement mocké)."""
    from app.core.config import get_settings
    import app.openmetadata.pipeline_service as ps

    monkeypatch.setenv("OPENMETADATA_ENABLED", "true")
    get_settings.cache_clear()
    ps.ensure_pipeline_service.cache_clear()

    fake_client = MagicMock()
    fake_service_entity = MagicMock()
    fake_service_entity.fullyQualifiedName = "hr-agent-pipeline-service"
    fake_client.create_or_update.return_value = fake_service_entity

    with patch("app.openmetadata.pipeline_service.get_client", return_value=fake_client):
        result = ps.ensure_pipeline_service()

    fake_client.create_or_update.assert_called_once()
    assert result is fake_service_entity

    ps.ensure_pipeline_service.cache_clear()
    monkeypatch.setenv("OPENMETADATA_ENABLED", "false")
    get_settings.cache_clear()
