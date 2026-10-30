from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AllocationSummary(BaseModel):
    """Allocation summary for cost evidence."""
    model_config = ConfigDict(from_attributes=True)
    evidence_id: str
    total_allocated: float
    allocation_count: int
    allocations: list[dict[str, Any]]


class AllocationItem(BaseModel):
    """Single allocation item."""
    workflow_run_id: str
    amount: float
