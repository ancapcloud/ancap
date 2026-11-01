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
