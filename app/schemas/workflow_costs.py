"""Evidence input for offline reconciliation; never accepts estimated costs."""
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_serializer, model_serializer
from pydantic.json import pydantic_encoder
import json

# Custom JSON encoder that handles Decimal
def decimal_encoder(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return pydantic_encoder(obj)

CostCategory = Literal["model", "data", "infrastructure", "review", "support", "payment_fee", "creator_payout"]
COST_CATEGORIES = ("model", "data", "infrastructure", "review", "support", "payment_fee", "creator_payout")


class ReconciledCostAllocation(BaseModel):
    model_config = ConfigDict(
        extra="forbid", 
        frozen=True
    )
    
    @field_serializer('allocated_amount')
    def serialize_allocated_amount(self, value: Decimal):
        return float(value)

    workflow_run_id: UUID
    category: CostCategory
    # A source line may be split across runs, but may only be allocated once per run.
    evidence_line_id: str = Field(min_length=1, max_length=200, pattern=r"^\S(?:.*\S)?$")
    evidence_amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)
    allocated_amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)
    currency: str = Field(pattern=r"^(?:[A-Z]{3,10}|wACP|sACP)$")


class ReconciledRunCosts(BaseModel):
    model_config = ConfigDict()
    
    @field_serializer('totals_by_currency')
    def serialize_totals_by_currency(self, value: dict[str, Decimal]):
        return {k: float(v) for k, v in value.items()}

    workflow_run_id: UUID
    totals_by_currency: dict[str, Decimal]
    evidenced_categories: list[CostCategory]
    missing_categories: list[CostCategory]
    coverage_complete: bool
    costs_are_independently_verified: Literal[False] = False


class CostRunAllocation(BaseModel):
    model_config = ConfigDict(
        extra="forbid", 
        frozen=True
    )
    
    @field_serializer('allocated_amount')
    def serialize_allocated_amount(self, value: Decimal):
        return float(value)

    workflow_run_id: UUID
    allocated_amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)


class CostEvidenceCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid", 
        frozen=True
    )
    
    @field_serializer('amount')
    def serialize_amount(self, value: Decimal):
        return float(value)

    source: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    document_id: str = Field(min_length=1, max_length=200, pattern=r"^\S(?:.*\S)?$")
    line_id: str = Field(min_length=1, max_length=100, pattern=r"^\S(?:.*\S)?$")
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    category: CostCategory
    currency: str = Field(pattern=r"^(?:[A-Z]{3,10}|wACP|sACP)$")
    amount: Decimal = Field(ge=0, max_digits=36, decimal_places=18, allow_inf_nan=False)
    review_note: str = Field(min_length=1, max_length=2000, pattern=r"^\S(?:.*\S)?$")
    allocations: list[dict] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def valid_distribution(self):
        from decimal import localcontext
        # allocations is now list[dict], access fields directly
        ids = [a.get("workflow_run_id") for a in self.allocations]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate run allocation")
        with localcontext() as context:
            context.prec = 80
            # Convert floats to Decimal for proper comparison
            total_allocated = sum((Decimal(str(a.get("allocated_amount", 0))) for a in self.allocations), Decimal(0))
            if total_allocated > self.amount:
                raise ValueError("Evidence line over-allocated")
        return self


class CostEvidenceReceipt(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_serialization_defaults_required=False, extra="forbid")
    
    @field_serializer('amount')
    def serialize_amount(self, value: Decimal):
        return float(value)

    id: UUID
    recorded_by_user_id: UUID | None
    # Operator attestation is deliberately distinct from an independent audit.
    verification_basis: Literal["operator_attested"] = "operator_attested"
    source: str
    document_id: str
    line_id: str
    document_sha256: str
    category: CostCategory
    currency: str
    amount: Decimal
    review_note: str
    allocations: list[dict]
    created_at: datetime | None = None


class CostEvidenceAdminResponse(BaseModel):
    """Admin-only response for cost evidence verification."""
    model_config = ConfigDict(from_attributes=True, json_schema_serialization_defaults_required=False)
    
    @field_serializer('amount')
    def serialize_amount(self, value: Decimal):
        return float(value)

    id: UUID
    recorded_by_user_id: UUID | None
    # Operator attestation is deliberately distinct from an independent audit.
    verification_basis: str
    source: str
    document_id: str
    line_id: str
    document_sha256: str
    category: CostCategory
    currency: str
    amount: Decimal
    review_note: str
    allocations: list[dict]
    created_at: datetime | None = None
    # External evidence source and metadata
    source_url: str | None = None
    author: str | None = None
    distributions: dict | None = None
