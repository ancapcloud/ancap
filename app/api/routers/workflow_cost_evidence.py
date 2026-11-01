"""Admin-only cost evidence retrieval endpoint.

GET /v1/workflow-store/admin/cost-evidence/{evidence_id}
- Admin-only access (require_platform_admin)
- Returns full cost evidence record with allocations
- Cache-Control: private, no-store
- Guest 401, regular user 403, unknown ID 404
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select

from app.api.deps import DbSession, require_platform_admin
from app.db.models import WorkflowCostEvidence
from app.services.workflow_costs import get_cost_evidence

router = APIRouter(prefix="/workflow-store", tags=["Workflow Cost Evidence Admin"])


@router.get(
    "/admin/cost-evidence/{evidence_id}",
    response_model=dict,
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
    session: DbSession,
    _admin_user_id: Annotated[str, Depends(require_platform_admin)],
    response: Response,
):
    """Admin-only endpoint to retrieve cost evidence by ID."""
    response.headers["Cache-Control"] = "private, no-store"

    evidence = (
        await session.execute(select(WorkflowCostEvidence).where(WorkflowCostEvidence.id == evidence_id))
    ).scalar_one_or_none()

    if evidence is None:
        raise HTTPException(status_code=404, detail="Cost evidence not found")

    receipt = await get_cost_evidence(evidence_id, session)

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
        "provider_id": receipt.provider_id,
        "document_type": receipt.document_type,
        "external_payment_event": receipt.external_payment_event,
        "delivery_event": receipt.delivery_event,
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
