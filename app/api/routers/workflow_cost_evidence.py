"""Admin-only endpoint for operator-attested cost evidence (COST-03).

GET /v1/workflow-store/admin/cost-evidence/{evidence_id}
- Admin-only: platform admin required, guest 401, user 403
- Returns full evidence record with allocations and ROP-04 fields
- Cache-Control: private, no-store
- verification_basis=operator_attested
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy import select
from app.api.deps import DbSession, require_platform_admin
from app.schemas.workflow_costs import CostEvidenceReceipt, ReconciledCostAllocation
from app.services.workflow_costs import get_cost_evidence

router = APIRouter(prefix="/workflow-store", tags=["Workflow Cost Evidence Admin"])


@router.get("/cost-evidence/{evidence_id}", response_model=CostEvidenceReceipt)
async def admin_get_cost_evidence(evidence_id: UUID, session: DbSession, response: Response,
                                  _admin: str = Depends(require_platform_admin)):
    """Admin-only retrieval of operator-attested cost evidence.
    
    - Guest users: 401 Unauthorized
    - Regular users: 403 Forbidden
    - Unknown evidence_id: 404 Not Found
    - Cache-Control: private, no-store
    - verification_basis=operator_attested
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await get_cost_evidence(evidence_id, session)


@router.post("/cost-evidence/{evidence_id}/reconcile", tags=["COST-04 Payment Provenance"])
async def reconcile_provider_payment(
    evidence_id: UUID,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
    reconciliation_status: str | None = None,
    delivery_event: bool | None = None
):
    """Verify provider reconciliation for payment provenance (COST-04).
    
    Updates the evidence record with reconciliation status and delivery event.
    - reconciliation_status: pending/verified/failed
    - delivery_event: boolean flag for delivery completion
    """
    from app.db.models import WorkflowCostEvidence
    
    evidence = (await session.execute(select(WorkflowCostEvidence).where(
        WorkflowCostEvidence.id == evidence_id))).scalar_one_or_none()
    if evidence is None:
        raise HTTPException(status_code=404, detail="Cost evidence not found")
    
    # Update reconciliation status if provided
    if reconciliation_status:
        valid_statuses = {"pending", "verified", "failed"}
        if reconciliation_status.lower() not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid reconciliation_status. Must be one of: {', '.join(valid_statuses)}")
        evidence.reconciliation_status = reconciliation_status
    
    # Update delivery event if provided
    if delivery_event is not None:
        evidence.delivery_event = delivery_event
    
    await session.flush()
    
    receipt = await get_cost_evidence(evidence_id, session)

    payload = receipt.model_dump()
    payload["reconciliation_status"] = (
        reconciliation_status or evidence.reconciliation_status
    )
    payload["delivery_status"] = (
        "verified"
        if (evidence.delivery_event and evidence.external_payment_event)
        else "pending"
    )
    return CostEvidenceReceipt(**payload)


@router.post("/cost-evidence/{evidence_id}/attribute", tags=["COST-05 Actual Cost Attribution"], response_model=CostEvidenceReceipt)
async def attribute_costs(
    evidence_id: UUID,
    body: dict,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    """Attribute costs to specific categories with provider billing and manual-work evidence (COST-05).
    
    Accepts cost attribution data including model/data/infrastructure costs, retry costs,
    review/support costs, payment fees. Validates currency separation and prevents double-counting
    creator payouts.
    
    - model_data_cost: costs for model inference and data processing
    - retry_cost: costs from failed retries
    - review_support_cost: manual review and support costs
    - payment_fee: payment processing fees
    """
    from app.services.workflow_costs import attribute_cost_evidence
    
    result = await attribute_cost_evidence(session, evidence_id, body)
    return result
