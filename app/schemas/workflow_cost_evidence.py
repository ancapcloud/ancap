from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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
