"""Pydantic schemas for ROP-05 packet templates (not onboarding templates)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PacketTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=120)
    description: str | None = None
    source_categories: list[str] = Field(default_factory=list)
    max_sources_per_packet: int = Field(default=10, ge=1, le=50)
    max_snapshots_per_source: int = Field(default=20, ge=1, le=100)
    max_claims_per_source: int = Field(default=50, ge=1, le=200)
    check_cooldown_seconds: int = Field(default=60, ge=1, le=3600)
    retention_days: int = Field(default=30, ge=1, le=365)
    packet_structure: dict[str, Any] = Field(default_factory=dict)
    languages: str = Field(default="en", pattern=r"^(en|ru|uk|de|zh-Hant)$")
    status: str = Field(default="draft", pattern=r"^(draft|active|archived)$")


class PacketTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID | None
    name: str
    slug: str
    description: str | None
    version: int
    source_categories: list[str]
    max_sources_per_packet: int
    max_snapshots_per_source: int
    max_claims_per_source: int
    check_cooldown_seconds: int
    retention_days: int
    packet_structure: dict[str, Any]
    languages: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PacketTemplateListResponse(BaseModel):
    templates: list[PacketTemplateResponse]
    total: int
