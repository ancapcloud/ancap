from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.common import Money

Verdict = Literal["accepted", "revision_requested", "rejected"]


class AssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    verdict: Verdict
    baseline_minutes: Decimal | None = Field(default=None, ge=0, le=1000000, max_digits=12, decimal_places=2, allow_inf_nan=False)
    assisted_minutes: Decimal | None = Field(default=None, ge=0, le=1000000, max_digits=12, decimal_places=2, allow_inf_nan=False)
    hourly_rate: Decimal | None = Field(default=None, ge=0, le=1000000000, max_digits=18, decimal_places=6, allow_inf_nan=False)
    hourly_currency: str | None = Field(default=None, pattern=r"^[A-Za-z][A-Za-z0-9]{1,9}$")
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("hourly_currency")
    @classmethod
    def normalize_unit(cls, value):
        if value is None:
            return None
        return {"wacp": "wACP", "sacp": "sACP"}.get(value.lower(), value.upper())

    @model_validator(mode="after")
    def paired_estimates(self):
        if (self.baseline_minutes is None) != (self.assisted_minutes is None):
            raise ValueError("Both time estimates are required together")
        if (self.hourly_rate is None) != (self.hourly_currency is None):
            raise ValueError("Hourly rate and unit are required together")
        if self.hourly_rate is not None and self.baseline_minutes is None:
            raise ValueError("Labor valuation requires both time estimates")
        return self


class AssessmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workflow_run_id: str
    result_hash: str
    verdict: Verdict
    baseline_minutes: Decimal | None = None
    assisted_minutes: Decimal | None = None
    hourly_rate: Decimal | None = None
    hourly_currency: str | None = None
    note: str | None = None
    created_at: datetime


class AssessmentState(BaseModel):
    result_hash: str
    assessment: AssessmentPublic | None = None
    has_stale_assessment: bool = False


class ValueSummary(BaseModel):
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
    estimated_labor_value: list[Money]
    ledger_charges: list[Money]
    estimates_are_self_reported: Literal[True] = True
    ledger_charges_are_verified_external_payments: Literal[False] = False
    scope_basis: Literal["completed_runs_created_in_window"] = "completed_runs_created_in_window"


class AssessmentHistory(BaseModel):
    items: list[AssessmentPublic]
    has_more: bool


class AssessedResultPublic(BaseModel):
    assessment_id: str
    result_hash: str
    result: Any


class CostEvidencePublic(BaseModel):
    """Admin view for cost evidence verification."""
    model_config = ConfigDict(from_attributes=True)
    evidence_id: str
    document_sha256: str
    source_url: str | None = None
    created_at: datetime
    author: str | None = None
    review_note: str | None = None
    distributions: list[dict[str, Any]] | None = None
    verification_basis: Literal["operator_attested"] = "operator_attested"
