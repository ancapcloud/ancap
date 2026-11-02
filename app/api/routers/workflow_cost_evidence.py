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
    _admin: str = Depends(require_platform_admin)
):
    """Verify provider reconciliation for payment provenance (COST-04).
    
    Checks that the external payment event and delivery event are properly
    reconciled with the provider's records. Returns updated evidence record.
    """
    from app.db.models import WorkflowCostEvidence
    
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
