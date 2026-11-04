"""Pydantic schemas for ROP-04 renewal events."""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RenewalEventCreate(BaseModel):
    """Request schema for creating a renewal event."""
    project_id: str = Field(..., description="Project identifier")
    client_id: str = Field(..., description="Client identifier")
    subscription_id: Optional[str] = Field(None, description="Optional internal subscription ID")
    renewal_type: str = Field(default="monthly", description="e.g., 'annual', 'monthly', 'license'")
    due_date: Optional[datetime] = Field(None, description="Due date for renewal")
    amount_due: Optional[float] = Field(None, description="Amount due for renewal")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")
    status: str = Field(default="pending", description="Status: pending, paid, failed, cancelled")
    payment_intent_id: Optional[str] = Field(None, description="Stripe/PaymentIntent ID if paid")
    event_metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "title": "RenewalEventCreate",
            "description": "Create a renewal event for subscription/license renewals (ROP-04)"
        }
    )


class RenewalEventUpdate(BaseModel):
    """Request schema for updating a renewal event."""
    actual_renewal_date: Optional[datetime] = Field(None, description="Actual renewal date when paid")
    status: Optional[str] = Field(None, description="New status: pending, paid, failed, cancelled")
    payment_intent_id: Optional[str] = Field(None, description="PaymentIntent ID if paid")
    event_metadata: Optional[dict[str, Any]] = Field(None, description="Updated metadata")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "title": "RenewalEventUpdate",
            "description": "Update fields of a renewal event"
        }
    )


class RenewalEventResponse(BaseModel):
    """Response schema for a renewal event."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    project_id: str
    client_id: str
    subscription_id: Optional[str]
    renewal_type: str
    due_date: datetime
    actual_renewal_date: Optional[datetime]
    amount_due: float
    currency: str
    status: str
    payment_intent_id: Optional[str]
    event_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "title": "RenewalEventResponse",
            "description": "Full renewal event record with ROP-04 fields"
        }
    )


class RenewalEventListResponse(BaseModel):
    """Response schema for listing renewal events."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[RenewalEventResponse]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(
        json_schema_extra={
            "title": "RenewalEventListResponse",
            "description": "Paginated list of renewal events"
        }
    )


class RenewalEventReceipt(BaseModel):
    """Receipt schema for renewal event processing."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_id: UUID
    project_id: str
    client_id: str
    status: str
    reconciliation_status: Optional[str] = Field(None, description="Reconciliation status from COST-06")
    delivery_status: Optional[str] = Field(None, description="Delivery status for external payment")
    amount_due: float
    currency: str
    processed_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "title": "RenewalEventReceipt",
            "description": "Receipt for renewal event with reconciliation and delivery status"
        }
    )
