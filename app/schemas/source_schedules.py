"""Pydantic schemas for source schedules (ROP-03)."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SourceScheduleCreate(BaseModel):
    """Schema for creating a source schedule."""
    model_config = ConfigDict(from_attributes=True)
    
    project_id: str = Field(..., max_length=255, description="Project identifier")
    source_type: str = Field(..., max_length=100, description="Source type (e.g., crypto-client, competitor)")
    source_pattern: Optional[str] = Field(None, max_length=512, description="Regex or glob pattern for sources")
    check_interval_minutes: int = Field(60, ge=1, le=1440, description="Check interval in minutes")
    retention_days: int = Field(30, ge=1, le=365, description="Source retention period")
    max_sources: int = Field(10, ge=1, description="Maximum sources to track")
    max_snapshots_per_source: int = Field(20, ge=1, description="Max snapshots per source")
    max_claims_per_source: int = Field(50, ge=1, description="Max claims per source")
    check_cooldown_seconds: int = Field(60, ge=1, description="Cooldown between checks")
    enabled: bool = Field(True, description="Whether schedule is active")


class SourceScheduleResponse(BaseModel):
    """Schema for source schedule response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    project_id: str
    source_type: str
    source_pattern: Optional[str]
    check_interval_minutes: int
    retention_days: int
    max_sources: int
    max_snapshots_per_source: int
    max_claims_per_source: int
    check_cooldown_seconds: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class SourceScheduleListResponse(BaseModel):
    """Schema for paginated source schedules list."""
    model_config = ConfigDict(from_attributes=True)
    
    schedules: List[SourceScheduleResponse]
    total: int
    limit: int
    offset: int
