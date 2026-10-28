"""Pydantic schemas for Research Operations admin endpoints."""
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CostEvidenceAdminView(BaseModel):
    """Admin-only view of cost evidence for operator verification.

    No mutations allowed. verification_basis is always 'operator_attested'.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    recorded_by_user_id: UUID | None
    source: str
    document_id: str
    line_id: str
    document_sha256: str
    category: str
    currency: str
    amount: Decimal
    review_note: str
    verification_basis: Literal["operator_attested"] = "operator_attested"
