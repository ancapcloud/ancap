"""Admin mutation endpoints for cost evidence (COST-04 / COST-05).

Canonical read path for COST-03 remains:
GET /v1/workflow-store/admin/cost-evidence/{evidence_id}
in app.api.routers.workflow_value — do not register a second GET here.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_platform_admin
from app.schemas.workflow_costs import CostEvidenceReceipt
from app.services.workflow_costs import get_cost_evidence

router = APIRouter(prefix="/workflow-store", tags=["Workflow Cost Evidence Admin"])


@router.post("/admin/cost-evidence/{evidence_id}/reconcile", tags=["COST-04 Payment Provenance"])
async def reconcile_provider_payment(
    evidence_id: UUID,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
    reconciliation_status: str | None = None,
    delivery_event: bool | None = None,
):
    """Verify provider reconciliation for payment provenance (COST-04).

    Updates the evidence record with reconciliation status and delivery event.
    - reconciliation_status: pending/verified/failed
    - delivery_event: boolean flag for delivery completion
    """
    from app.db.models import WorkflowCostEvidence

    evidence = (
        await session.execute(
            select(WorkflowCostEvidence).where(WorkflowCostEvidence.id == evidence_id)
        )
    ).scalar_one_or_none()
    if evidence is None:
        raise HTTPException(status_code=404, detail="Cost evidence not found")

    if reconciliation_status:
        valid_statuses = {"pending", "verified", "failed"}
        if reconciliation_status.lower() not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reconciliation_status. Must be one of: {', '.join(sorted(valid_statuses))}",
            )
        evidence.reconciliation_status = reconciliation_status

    if delivery_event is not None:
        evidence.delivery_event = delivery_event

    await session.flush()

    receipt = await get_cost_evidence(evidence_id, session)
    payload = receipt.model_dump()
    payload["reconciliation_status"] = reconciliation_status or evidence.reconciliation_status
    payload["delivery_status"] = (
        "verified"
        if (evidence.delivery_event and evidence.external_payment_event)
        else "pending"
    )
    return CostEvidenceReceipt(**payload)


@router.post(
    "/admin/cost-evidence/{evidence_id}/attribute",
    tags=["COST-05 Actual Cost Attribution"],
    response_model=CostEvidenceReceipt,
)
async def attribute_costs(
    evidence_id: UUID,
    body: dict,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    """Attribute costs to categories with provider billing and manual-work evidence (COST-05)."""
    from app.services.workflow_costs import attribute_cost_evidence

    return await attribute_cost_evidence(session, evidence_id, body)
