"""Evidence input for offline reconciliation; never accepts estimated costs."""
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
