"""
Configuration centrale de l'application, via Pydantic Settings.

Toute la config vient de variables d'environnement (.env) — jamais de
secret en dur dans le code. Voir .env.example à la racine pour la liste
complète des variables et leur description.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Application ---
    app_name: str = "HR Pipeline Platform"
    environment: str = Field(default="development")
    api_key: str = Field(default="dev-local-key-change-me")
    cors_allow_origins: str = Field(default="*")  # séparés par des virgules
    rate_limit_per_minute: int = Field(default=120)

    # --- Base de données ---
    database_url: str = Field(
        default="sqlite:///./hr_pipeline.db",
        description="URL SQLAlchemy. Ex MySQL: mysql+pymysql://user:pwd@host:3306/hr_pipeline",
    )

    # --- LLM ---
    # --- LLM ---
    llm_provider: str = Field(default="none")  # none | anthropic | openai | groq
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    llm_model: str | None = None

    # --- Audit / RGPD ---
    audit_pseudonymization_salt: str = Field(default="change-me-in-production")
    audit_log_retention_days: int = 365

    # --- Prometheus ---
    prometheus_port: int = 8000

    # --- OpenMetadata ---
    openmetadata_enabled: bool = False
    openmetadata_host_port: str = "http://localhost:8585/api"
    openmetadata_jwt_token: str | None = None

    # --- Règles métier (voir aussi app/core/rules.py pour le détail) ---
    min_years_experience: int = 1
    min_required_skills_matched_ratio: float = 0.5
    min_score_for_onboarding: float = 60.0

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
