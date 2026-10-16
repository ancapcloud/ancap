"""Pydantic schemas for People + AI project economy (Wave 1)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProjectStatus = Literal["draft", "published", "archived"]
ProjectKind = Literal["concept", "demo", "community"]
AssigneeType = Literal["human", "agent", "either"]
ApplicationStatus = Literal["pending", "accepted", "rejected"]


class EconomyTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    acceptance_criteria: str = Field(min_length=1, max_length=4000)
    stage_order: int = Field(default=0, ge=0, le=1000)
    price_acp: Decimal | None = Field(default=None, ge=0, max_digits=36, decimal_places=18)
    assignee_type: AssigneeType = "human"


class EconomyProjectCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=4000)
    result_promise: str = Field(min_length=1, max_length=4000)
    earning_model: str | None = Field(default=None, max_length=2000)
    kind: ProjectKind = "community"
    background_href: str | None = Field(default=None, max_length=200)
    tasks: list[EconomyTaskCreate] = Field(default_factory=list, max_length=40)

    @field_validator("slug")
    @classmethod
    def _slug(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if not normalized or any(ch for ch in normalized if not (ch.isalnum() or ch in "-_")):
            raise ValueError("slug must be lowercase alphanumeric with optional -/_")
        return normalized


class EconomyProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    summary: str | None = Field(default=None, min_length=1, max_length=4000)
    result_promise: str | None = Field(default=None, min_length=1, max_length=4000)
    earning_model: str | None = Field(default=None, max_length=2000)
    kind: ProjectKind | None = None
    background_href: str | None = Field(default=None, max_length=200)


class EconomyApplicationCreate(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class EconomyTaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    acceptance_criteria: str
    stage_order: int
    price_acp: Decimal | None = None
    assignee_type: AssigneeType
    created_at: datetime


class EconomyApplicationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    applicant_user_id: UUID
    status: ApplicationStatus
    note: str | None = None
    created_at: datetime


class EconomyProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID | None = None
    owner_display_name: str | None = None
    slug: str
    title: str
    summary: str
    result_promise: str
    earning_model: str | None = None
    status: ProjectStatus
    kind: ProjectKind
    seed_key: str | None = None
    is_platform_seed: bool = False
    background_href: str | None = None
    metadata_json: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    tasks: list[EconomyTaskPublic] = Field(default_factory=list)


class EconomyProjectListResponse(BaseModel):
    items: list[EconomyProjectPublic]
    total: int
    mutations_enabled: bool
    preview_only: bool
