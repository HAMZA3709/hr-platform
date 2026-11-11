"""Erreurs applicatives typées, converties en réponses HTTP cohérentes par l'API."""

from __future__ import annotations


class AppError(Exception):
    """Erreur applicative de base."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ValidationAppError(AppError):
    status_code = 422
    error_code = "validation_error"


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "unauthorized"


class RateLimitedError(AppError):
    status_code = 429
    error_code = "rate_limited"


class DependencyUnavailableError(AppError):
    """Une dépendance externe (OpenMetadata, LLM...) est indisponible.

    Ne doit JAMAIS empêcher le pipeline RH lui-même de fonctionner — utilisée
    uniquement pour signaler l'état dans les endpoints /health/*.
    """

    status_code = 503
    error_code = "dependency_unavailable"
