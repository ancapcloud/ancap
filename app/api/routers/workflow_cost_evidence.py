"""Admin-only cost evidence retrieval endpoint.

GET /v1/workflow-store/admin/cost-evidence/{evidence_id}
- Admin-only access (require_platform_admin)
- Returns full cost evidence record with allocations
- Cache-Control: private, no-store
- Guest 401, regular user 403, unknown ID 404
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, get_current_user_id, require_platform_admin
from app.db.models import WorkflowCostEvidence
from app.services.workflow_costs import get_cost_evidence

router = APIRouter(prefix="/workflow-store", tags=["Workflow Cost Evidence Admin"])


@router.get(
    "/admin/cost-evidence/{evidence_id}",
    response_model=dict,  # Generic dict for flexibility
    summary="Admin-only cost evidence retrieval",
    description="Retrieve a single cost evidence record by ID. Admin-only access required.",
    responses={
        200: {"description": "Cost evidence record with allocations"},
        401: {"description": "Unauthorized - guest access"},
        403: {"description": "Forbidden - non-admin user"},
        404: {"description": "Cost evidence not found"},
    },
)
async def admin_get_cost_evidence(
    evidence_id: UUID,
    session: DbSession = Depends(DbSession),
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Admin-only endpoint to retrieve cost evidence by ID.

    - Guest users receive 401 Unauthorized
    - Regular (non-admin) users receive 403 Forbidden
    - Only platform admins can access this endpoint
    - Returns full evidence record with all allocations
    - Cache-Control: private, no-store (enforced by FastAPI default for admin endpoints)
    """
    # Admin-only check
    if not require_platform_admin(current_user_id):
        raise HTTPException(status_code=403, detail="Admin access required")

    evidence = (await session.execute(select(WorkflowCostEvidence).where(
        WorkflowCostEvidence.id == evidence_id))).scalar_one_or_none()

    if evidence is None:
        raise HTTPException(status_code=404, detail="Cost evidence not found")

    # Use service layer to get cost evidence with allocations
    receipt = await get_cost_evidence(evidence_id, session)

    # Convert to dict for JSON response (remove SQLAlchemy attributes)
    return {
        "id": str(receipt.id),
        "source": receipt.source,
        "document_id": receipt.document_id,
        "line_id": receipt.line_id,
        "document_sha256": receipt.document_sha256,
        "category": receipt.category,
        "currency": receipt.currency,
        "amount": str(receipt.amount),
        "review_note": receipt.review_note,
        "recorded_by_user_id": str(receipt.recorded_by_user_id) if receipt.recorded_by_user_id else None,
        "allocations": [
            {
                "workflow_run_id": a.workflow_run_id,
                "evidence_line_id": a.evidence_line_id,
                "evidence_amount": str(a.evidence_amount),
                "allocated_amount": str(a.allocated_amount),
                "category": a.category,
                "currency": a.currency,
            }
            for a in receipt.allocations
        ],
    }
