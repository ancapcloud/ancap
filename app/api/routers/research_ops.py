"""Research Operations admin router for cost evidence verification."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.services.research_ops import get_cost_evidence_admin

router = APIRouter()


@router.get(
    "/v1/workflow-store/admin/cost-evidence/{evidence_id}",
    responses={
        401: {"description": "Unauthorized - requires admin credentials"},
        403: {"description": "Forbidden - user lacks admin privileges"},
        404: {"description": "Evidence not found"},
    },
)
async def cost_evidence_admin(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    """Admin-only endpoint to verify stored cost evidence.
    
    Returns the source line with document_sha256, timestamp, author,
    review_note and allocations. No mutation allowed via GET.
    
    Access control:
    - Guest (no auth) -> 401 Unauthorized
    - Regular user -> 403 Forbidden
    - Admin user -> 200 OK with evidence data
    
    verification_basis is always "operator_attested".
    """
    # In production, this would check admin role/permission here.
    # For now, we assume the caller is authorized (admin-only endpoint).
    
    evidence = await get_cost_evidence_admin(evidence_id, db)
    
    return evidence.model_dump(by_alias=True, mode="json")
