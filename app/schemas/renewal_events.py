"""Pydantic schemas for ROP-04 renewal events."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class RenewalEventCreate(BaseModel):
    """Schema for creating a renewal event."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    project_id: str = Field(..., min_length=1, max_length=255)
    client_id: str = Field(..., min_length=1, max_length=255)
    subscription_id: Optional[str] = Field(None, max_length=255)
    renewal_type: str = Field(..., pattern=r"^(annual|monthly|license)$")
    due_date: datetime
    amount_due: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="pending", pattern=r"^(pending|paid|failed|cancelled)$")
    payment_intent_id: Optional[str] = Field(None, max_length=255)
    event_metadata: Optional[Dict[str, Any]] = None


class RenewalEventUpdate(BaseModel):
    """Schema for updating a renewal event."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    actual_renewal_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern=r"^(pending|paid|failed|cancelled)$")
    payment_intent_id: Optional[str] = Field(None, max_length=255)
    event_metadata: Optional[Dict[str, Any]] = None


class RenewalEventResponse(BaseModel):
    """Schema for renewal event response."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    project_id: str
    client_id: str
    subscription_id: Optional[str]
    renewal_type: str
    due_date: datetime
    actual_renewal_date: Optional[datetime]
    amount_due: Decimal
    currency: str
    status: str
    payment_intent_id: Optional[str]
    event_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
