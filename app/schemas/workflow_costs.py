"""Evidence input for offline reconciliation; never accepts estimated costs."""
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

CostCategory = Literal["model", "data", "infrastructure", "review", "support", "payment_fee", "creator_payout"]
COST_CATEGORIES = ("model", "data", "infrastructure", "review", "support", "payment_fee", "creator_payout")


class ReconciledCostAllocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workflow_run_id: UUID
    category: CostCategory
    # A source line may be split across runs, but may only be allocated once per run.
    evidence_line_id: str = Field(min_length=1, max_length=200, pattern=r"^\S(?:.*\S)?$")
    evidence_amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)
    allocated_amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)
    currency: str = Field(pattern=r"^(?:[A-Z]{3,10}|wACP|sACP)$")


class ReconciledRunCosts(BaseModel):
    workflow_run_id: UUID
    totals_by_currency: dict[str, Decimal]
    evidenced_categories: list[CostCategory]
    missing_categories: list[CostCategory]
    coverage_complete: bool
    costs_are_independently_verified: Literal[False] = False


class CostRunAllocation(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    workflow_run_id: UUID
    allocated_amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)
    evidence_line_id: str | None = None
    evidence_amount: Decimal | None = None
    category: CostCategory | None = None
    currency: str | None = None


class CostEvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    document_id: str = Field(min_length=1, max_length=200, pattern=r"^\S(?:.*\S)?$")
    line_id: str = Field(min_length=1, max_length=100, pattern=r"^\S(?:.*\S)?$")
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    category: CostCategory
    currency: str = Field(pattern=r"^(?:[A-Z]{3,10}|wACP|sACP)$")
    amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)
    review_note: str = Field(min_length=1, max_length=2000, pattern=r"^\S(?:.*\S)?$")
    allocations: list[CostRunAllocation] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def valid_distribution(self):
        from decimal import localcontext
        ids = [a.workflow_run_id for a in self.allocations]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate run allocation")
        with localcontext() as context:
            context.prec = 80
            if sum((a.allocated_amount for a in self.allocations), Decimal(0)) > self.amount:
                raise ValueError("Evidence line over-allocated")
        return self


class CostEvidenceReceipt(BaseModel):
    id: UUID
    recorded_by_user_id: UUID | None
    # Operator attestation is deliberately distinct from an independent audit.
    verification_basis: Literal["operator_attested"] = "operator_attested"
    allocations: list[ReconciledCostAllocation] = []
    source: str | None = None
    document_id: str | None = None
    line_id: str | None = None
    document_sha256: str | None = None
    category: CostCategory | None = None
    currency: str | None = None
    amount: Decimal | None = None
    review_note: str | None = None
    # ROP-04 fields for provider reconciliation and external events
    provider_id: str | None = None
    document_type: str | None = None
    external_payment_event: bool = False
    delivery_event: bool = False


class QualityFixturePublic(BaseModel):
    """Quality fixture record for admin-only retrieval."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    fixture_type: str
    language: str
    sample_id: str
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    confidence_score: Optional[float] = None
    is_available: bool
    created_at: str  # ISO timestamp
    expires_at: Optional[str] = None


class QualityFixtureCreate(BaseModel):
    """Admin-only fixture creation."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    fixture_type: str = Field(pattern=r"^(?:price_change|markup_noise|unavailable_source|contradiction|malicious_instructions)$")
    language: str = Field(pattern=r"^[a-zA-Z-]{2,10}$")
    sample_id: str = Field(min_length=1, max_length=64)
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    confidence_score: Optional[float] = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    is_available: bool = True
    expires_at: Optional[str] = None
