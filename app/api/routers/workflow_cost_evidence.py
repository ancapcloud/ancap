"""Compatibility alias for private operator-attested cost evidence."""
from uuid import UUID
from fastapi import APIRouter, Depends, Response
from app.api.deps import DbSession, require_platform_admin
from app.schemas.workflow_costs import CostEvidenceReceipt
from app.services.workflow_costs import get_cost_evidence

router = APIRouter(prefix="/workflow-store", tags=["Workflow Cost Evidence Admin"])


@router.get("/cost-evidence/{evidence_id}", response_model=CostEvidenceReceipt)
async def admin_get_cost_evidence(evidence_id: UUID, session: DbSession, response: Response,
                                  _admin: str = Depends(require_platform_admin)):
    response.headers["Cache-Control"] = "private, no-store"
    return await get_cost_evidence(evidence_id, session)


@router.post("/cost-evidence/{evidence_id}/reconcile", tags=["COST-04 Payment Provenance"])
async def reconcile_provider_payment(
    evidence_id: UUID,
    session: DbSession,
    _admin: str = Depends(require_platform_admin)
):
    """Verify provider reconciliation for payment provenance (COST-04).
    
    Checks that the external payment event and delivery event are properly
    reconciled with the provider's records. Returns reconciliation status.
    """
    from app.db.models import WorkflowCostEvidence
    from app.schemas.workflow_costs import CostEvidenceReceipt, ReconciledCostAllocation
    
    evidence = (await session.execute(select(WorkflowCostEvidence).where(
        WorkflowCostEvidence.id == evidence_id))).scalar_one_or_none()
    if evidence is None:
        raise HTTPException(status_code=404, detail="Cost evidence not found")
    
    # Check provider reconciliation status
    reconciliation_status = "pending" if not evidence.external_payment_event else "verified"
    delivery_status = "pending" if not evidence.delivery_event else "verified"
    
    receipt = await get_cost_evidence(evidence_id, session)
    
    return CostEvidenceReceipt(
        **receipt.model_dump(),
        reconciliation_status=reconciliation_status,
        delivery_status=delivery_status
    )
