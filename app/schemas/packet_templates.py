"""Pydantic schemas for packet templates (ROP-06)."""

from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class PacketTemplateCreate(BaseModel):
    """Request schema for creating a packet template."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    source_categories: List[str] = Field(default_factory=list)
    max_sources_per_packet: int = Field(default=10, ge=1, le=50)
    max_snapshots_per_source: int = Field(default=20, ge=1, le=100)
    max_claims_per_source: int = Field(default=50, ge=1, le=200)
    check_cooldown_seconds: int = Field(default=60, ge=1, le=3600)
    retention_days: int = Field(default=30, ge=1, le=365)
    packet_structure: Dict[str, Any] = Field(default_factory=dict)
    languages: str = Field(default="en", pattern=r"^(en|ru|uk|de|zh-Hant)$")
    status: str = Field(default="draft", pattern=r"^(draft|active|archived)$")


class PacketTemplateUpdate(BaseModel):
    """Request schema for updating a packet template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    source_categories: Optional[List[str]] = None
    max_sources_per_packet: Optional[int] = Field(None, ge=1, le=50)
    max_snapshots_per_source: Optional[int] = Field(None, ge=1, le=100)
    max_claims_per_source: Optional[int] = Field(None, ge=1, le=200)
    check_cooldown_seconds: Optional[int] = Field(None, ge=1, le=3600)
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    packet_structure: Optional[Dict[str, Any]] = None
    languages: Optional[str] = Field(None, pattern=r"^(en|ru|uk|de|zh-Hant)$")
    status: Optional[str] = Field(None, pattern=r"^(draft|active|archived)$")


class PacketTemplateResponse(BaseModel):
    """Response schema for packet template retrieval."""
    id: UUID
    owner_user_id: Optional[UUID]
    name: str
    slug: str
    description: Optional[str]
    version: int
    source_categories: List[str]
    max_sources_per_packet: int
    max_snapshots_per_source: int
    max_claims_per_source: int
    check_cooldown_seconds: int
    retention_days: int
    packet_structure: Dict[str, Any]
    languages: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PacketTemplateListResponse(BaseModel):
    """Response schema for listing packet templates."""
    templates: List[PacketTemplateResponse]
    total: int
