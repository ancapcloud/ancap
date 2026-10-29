from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WindowDays = Literal[7, 14, 30, 90]


class ValueRequest(BaseModel):
    """Request for /ai/value endpoint to get value summary."""
    model_config = {"extra": "forbid"}
    days: WindowDays = Field(default=30, ge=7, le=90)


class ValueResponse(BaseModel):
    """Response from /ai/value endpoint."""
    window_start: datetime
    window_end: datetime
    days: int
    limit: int
    truncated: bool
    completed_count: int
    assessed_count: int
    accepted_count: int
    revision_requested_count: int
    rejected_count: int
    timed_assessment_count: int
    labor_valued_count: int
    estimated_minutes_saved: str | None
    estimated_labor_value: list[dict[str, str]]
    ledger_charges: list[dict[str, str]]
    estimates_are_self_reported: bool = True
    ledger_charges_are_verified_external_payments: bool = False
    scope_basis: Literal["completed_runs_created_in_window"] = "completed_runs_created_in_window"
