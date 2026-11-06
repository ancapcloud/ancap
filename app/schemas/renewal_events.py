"""Schemas for ROP-04 renewal events (admin-only economics evidence)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RenewalStatus = Literal["pending", "paid", "failed", "cancelled"]
RenewalType = Literal["monthly", "quarterly", "annual", "license", "one_off"]

# Exact decimal; serialized as a string so no client sees a float rounding.
_MAX_AMOUNT = Decimal("1000000000000000000")


class RenewalEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(..., min_length=1, max_length=255)
    client_id: str = Field(..., min_length=1, max_length=255)
    subscription_id: str | None = Field(None, max_length=255)
    renewal_type: RenewalType = "monthly"
    due_at: datetime
    amount_due: Decimal = Field(..., ge=0, le=_MAX_AMOUNT, max_digits=36, decimal_places=18)
    currency: str = Field("EUR", min_length=2, max_length=10, pattern=r"^[A-Za-z][A-Za-z0-9]{1,9}$")
    note: str | None = Field(None, max_length=2000)

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("due_at")
    @classmethod
    def _tz_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        return value


class RenewalEventStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["paid", "failed", "cancelled"]
    renewed_at: datetime | None = None
    payment_reference: str | None = Field(None, max_length=255)
    note: str | None = Field(None, max_length=2000)

    @field_validator("renewed_at")
    @classmethod
    def _tz_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("renewed_at must include a timezone")
        return value


class RenewalEventResponse(BaseModel):
    id: str
    project_id: str
    client_id: str
    subscription_id: str | None
    renewal_type: str
    due_at: datetime
    renewed_at: datetime | None
    amount_due: str
    currency: str
    status: str
    payment_reference: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime


class RenewalEventListResponse(BaseModel):
    events: list[RenewalEventResponse]
    total: int
    limit: int
    offset: int


class RenewalCurrencyTotals(BaseModel):
    currency: str
    due: str
    paid: str


class RenewalCohortSummary(BaseModel):
    """Measured due-renewal cohort. Rates are null until something resolved."""

    project_id: str | None
    due_from: datetime
    due_to: datetime
    total: int
    pending: int
    paid: int
    failed: int
    cancelled: int
    renewal_rate: str | None = Field(
        None, description="paid / (paid + failed + cancelled), 4 decimal places; null when nothing resolved"
    )
    totals: list[RenewalCurrencyTotals]
