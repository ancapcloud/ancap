"""Pydantic schemas for quality fixtures (ROP-03)."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class QualityFixtureCreate(BaseModel):
    """Schema for creating a quality fixture."""
    model_config = ConfigDict(from_attributes=True)
    
    fixture_type: str = Field(..., pattern=r"^(price_change|markup_noise|unavailable_source|contradiction|malicious_instructions)$", description="Type of fixture")
    language: str = Field(..., pattern=r"^(zh-Hant|en|ru|de|fr)$", max_length=10, description="Language code")
    sample_id: str = Field(..., max_length=64, description="Unique sample identifier")
    expected_result: Optional[str] = Field(None, description="Expected OCR output or verdict")
    actual_result: Optional[str] = Field(None, description="Actual OCR output from model")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model confidence 0.0-1.0")
    is_available: bool = Field(True, description="Source availability status")


class QualityFixtureResponse(BaseModel):
    """Schema for quality fixture response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    fixture_type: str
    language: str
    sample_id: str
    expected_result: Optional[str]
    actual_result: Optional[str]
    confidence_score: Optional[float]
    is_available: bool
    created_at: datetime
    expires_at: Optional[datetime]


class QualityFixtureListResponse(BaseModel):
    """Schema for paginated quality fixtures list."""
    model_config = ConfigDict(from_attributes=True)
    
    fixtures: List[QualityFixtureResponse]
    total: int
    limit: int
    offset: int
