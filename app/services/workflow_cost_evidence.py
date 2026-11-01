"""Service layer for cost evidence operations (COST-03).

Provides admin-only retrieval of operator-attested cost evidence with full allocations.
Never accepts estimated costs; always uses verified source data.
"""
from uuid import UUID
from sqlalchemy import select
from app.db.models import WorkflowCostEvidence


async def get_cost_evidence(evidence_id: UUID, session) -> dict:
    """Retrieve operator-attested cost evidence by ID (admin-only).
    
    Returns full evidence record with allocations and ROP-04 fields.
    Raises HTTPException 404 if not found.
    """
    result = await session.execute(select(WorkflowCostEvidence).where(
        WorkflowCostEvidence.id == evidence_id))
    row = result.scalar_one_or_none()
    
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Cost evidence not found")
    
    # Convert SQLAlchemy model to dict with all fields including ROP-04
    return {
        "id": str(row.id),
        "recorded_by_user_id": row.recorded_by_user_id,
        "verification_basis": row.verification_basis,
        "source": row.source,
        "document_id": row.document_id,
        "line_id": row.line_id,
        "document_sha256": row.document_sha256,
        "category": row.category,
        "currency": row.currency,
        "amount": str(row.amount),
        "review_note": row.review_note,
        "provider_id": row.provider_id,
        "document_type": row.document_type,
        "external_payment_event": row.external_payment_event,
        "delivery_event": row.delivery_event,
        "allocations": [
            {
                "workflow_run_id": str(a.workflow_run_id),
                "category": a.category,
                "evidence_line_id": a.evidence_line_id,
                "evidence_amount": str(a.evidence_amount),
                "allocated_amount": str(a.allocated_amount),
                "currency": a.currency,
            }
            for a in row.allocations
        ],
    }
