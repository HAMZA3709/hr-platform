"""Schémas Pydantic (entrée/sortie API)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CandidateCreate(BaseModel):
    candidate_ref: str = Field(..., description="Identifiant externe unique du candidat")
    years_experience: int = Field(..., ge=0)
    skills: list[str] = Field(default_factory=list)
    education_level: str | None = None
    job_offer_id: int | None = None
    cv_text: str = Field(default="", description="Texte du CV — traité comme donnée non fiable")


class CandidateOut(BaseModel):
    id: int
    candidate_ref: str
    years_experience: int
    education_level: str | None
    skills: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunOut(BaseModel):
    id: int
    run_id: str
    candidate_id: int
    correlation_id: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_ms: float | None

    model_config = {"from_attributes": True}


class DecisionOut(BaseModel):
    id: int
    pipeline_run_id: int
    ready: bool
    reason: str
    rules_applied: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    correlation_id: str | None = None
