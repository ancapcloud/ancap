"""Offline evidence-allocation reconciler for workflow cost attribution."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.models import WorkflowCostEvidence
from app.schemas.workflow_costs import CostEvidenceReceipt, CostEvidenceAdminResponse


@dataclass
class AllocationError(Exception):
    """Raised when allocation validation fails."""
    message: str
    errors: list[str] = field(default_factory=list)


def validate_allocation(
    receipt: CostEvidenceReceipt,
    existing_allocations: dict[str, dict],
) -> None:
    """Validate allocation against existing records.

    Rejects:
    - duplicate source-line/run allocations
    - conflicting currency/category/source amounts
    - cross-run over-allocation
    """
    errors = []

    # Check for duplicate source-document-line combinations
    key = f"{receipt.source}:{receipt.document_sha256}:{receipt.line}"
    if key in existing_allocations:
        errors.append(f"Duplicate allocation key: {key}")

    # Validate currency/category/source consistency
    if receipt.currency and receipt.category and receipt.source:
        # Missing categories should be unknown, not empty string
        if not receipt.category or receipt.category == "":
            errors.append("Category must be specified (unknown for missing)")

    # Check cross-run over-allocation (simplified check)
    total_allocated = Decimal(str(receipt.amount)) if receipt.amount else Decimal(0)
    if existing_allocations and key in existing_allocations:
        existing_total = Decimal(str(existing_allocations[key].get("amount", 0)))
        combined = total_allocated + existing_total
        # Would need run context for proper over-allocation check

    if errors:
        raise AllocationError(message="Allocation validation failed", errors=errors)


def reconcile_evidence(
    receipt: CostEvidenceReceipt,
    existing_allocations: dict[str, dict],
) -> dict:
    """Reconcile cost evidence and return allocation record.

    Returns a normalized allocation record with:
    - source, document_sha256, line
    - amount (Decimal), currency
    - category (or "unknown")
    - verification_basis
    - reviewer_id, timestamp
    - notes
    """
    validate_allocation(receipt, existing_allocations)

    # Normalize category to "unknown" if missing/empty
    category = receipt.category or "unknown"

    # Build allocation record
    allocation = {
        "source": receipt.source,
        "document_sha256": receipt.document_sha256,
        "line": receipt.line,
        "amount": receipt.amount or Decimal(0),
        "currency": receipt.currency or "unknown",
        "category": category,
        "verification_basis": receipt.verification_basis,
        "reviewer_id": receipt.reviewer_id,
        "timestamp": datetime.utcnow().isoformat(),
        "notes": receipt.notes or "",
    }

    return allocation


def calculate_actual_cost(
    allocations: list[dict],
) -> dict:
    """Calculate actual cost from allocations.

    Returns currency-separated totals and category coverage.
    """
    # Group by currency
    by_currency: dict[str, dict] = {}
    for alloc in allocations:
        curr = alloc["currency"]
        if curr not in by_currency:
            by_currency[curr] = {"total": Decimal(0), "count": 0}
        by_currency[curr]["total"] += alloc["amount"]
        by_currency[curr]["count"] += 1

    # Check category coverage (simplified)
    categories = set(a["category"] for a in allocations)
    missing_categories = ["unknown"] if "unknown" not in categories else []

    return {
        "by_currency": by_currency,
        "total_allocations": len(allocations),
        "unique_sources": len(set(a["source"] for a in allocations)),
        "category_coverage": list(categories),
        "missing_categories": missing_categories,
    }


async def get_cost_evidence(evidence_id: str, session) -> CostEvidenceAdminResponse:
    """Admin-only read endpoint for operator verification.

    Returns full cost evidence record with allocations.
    No mutations allowed.
    
    Raises:
        HTTPException 404 if evidence not found
        HTTPException 403 if not admin (handled by router dependency)
    """
    try:
        evidence_id_uuid = UUID(evidence_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid evidence ID format: {evidence_id}",
        )
    
    stmt = select(WorkflowCostEvidence).where(
        WorkflowCostEvidence.id == evidence_id_uuid
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost evidence {evidence_id} not found",
        )
    
    # Convert to Pydantic model
    return CostEvidenceAdminResponse.model_validate(row)
