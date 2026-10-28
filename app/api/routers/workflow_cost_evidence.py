"""Admin-only GET /v1/workflow-store/admin/cost-evidence/{evidence_id} for operator-attested verification."""
from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import JSONResponse

from app.api.deps import DbSession, get_current_user_id, require_platform_admin
from app.db.models import WorkflowCostEvidence, User
from app.schemas.workflow_costs import CostEvidenceReceipt

router = APIRouter(prefix="/workflow-store", tags=["Workflow Cost Evidence Admin"])


@router.get(
    "/admin/cost-evidence/{evidence_id}",
    response_model=CostEvidenceReceipt,
    dependencies=[Depends(require_platform_admin)],
    responses={
        401: {"description": "Unauthorized — requires platform admin token"},
        403: {"description": "Forbidden — authenticated but not platform admin"},
        404: {"description": "Evidence record not found"},
    },
)
async def get_cost_evidence(
    evidence_id: UUID,
    db: DbSession,
    current_user_id: UUID | None = Depends(get_current_user_id),
    x_forwarded_for: str | None = Header(None),
):
    """
    Admin-only read-only endpoint for operator-attested cost evidence verification.

    - **Access**: Platform admin only (enforced via `require_platform_admin`).
    - **Verification basis**: Always `operator_attested`.
    - **Cache**: `private, no-store` — never cached.
    - **Mutations**: None — GET only.
    - **Document loading**: Never fetches document from network; returns stored metadata only.

    Returns the full evidence record including source lines (allocations), SHA256, timestamp, author, and review note.
    """
    # Platform admin check is enforced by Depends(require_platform_admin) above.
    # If current_user_id is None or not a platform admin, FastAPI will raise 403 before this runs.

    evidence = db.get(WorkflowCostEvidence, evidence_id)
    if not evidence:
        return JSONResponse(status_code=404, content={"detail": "Evidence record not found"})

    # Build receipt response (no document fetch, no mutations)
    receipt = CostEvidenceReceipt(
        id=evidence.id,
        source=evidence.source,
        document_id=evidence.document_id,
        line_id=evidence.line_id,
        document_sha256=evidence.document_sha256,
        category=evidence.category,
        currency=evidence.currency,
        amount=float(evidence.amount),
        review_note=evidence.review_note,
        recorded_by_user_id=evidence.recorded_by_user_id,
        verification_basis=evidence.verification_basis,
        allocations=evidence.allocations,
        created_at=evidence.created_at.replace(tzinfo=timezone.utc) if evidence.created_at.tzinfo is None else evidence.created_at,
    )

    return receipt
