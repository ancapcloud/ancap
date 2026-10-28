"""Service layer for Research Operations admin endpoints.

Admin-only read operations for cost evidence verification.
No mutations allowed in this module.
"""
from uuid import UUID
from sqlalchemy import select
from fastapi import HTTPException, status

from app.db.models import WorkflowCostEvidence


async def get_cost_evidence_admin(evidence_id: UUID, session):
    """Read a single cost-evidence record for operator verification (admin-only).

    Returns the complete source line with document_sha256, time, author,
    review_note and allocations. No mutations allowed.
    verification_basis is always 'operator_attested'.
    
    Args:
        evidence_id: UUID of the cost evidence record
        session: SQLAlchemy async session
        
    Returns:
        WorkflowCostEvidence record as dict
        
    Raises:
        HTTPException: 404 if not found
    """
    row = (await session.execute(select(WorkflowCostEvidence).where(
        WorkflowCostEvidence.id == evidence_id))).scalar_one_or_none()
    
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost evidence not found"
        )
    
    return row
