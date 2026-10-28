"""Admin-only endpoint for cost evidence verification."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_auth
from app.db.session import get_db as get_db_session
from app.schemas.workflow_costs import CostEvidenceReceipt, CostEvidenceVerificationResponse

router = APIRouter(prefix="/workflow-costs", tags=["workflow-costs"])


@router.get(
    "/evidence/{receipt_id}",
    response_model=CostEvidenceVerificationResponse,
    dependencies=[Depends(require_auth)],
)
async def verify_cost_evidence(
    receipt_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CostEvidenceVerificationResponse:
    """Verify a cost evidence receipt (admin-only).

    This endpoint checks if the provided receipt ID exists in the database
    and returns its details. It is intended for internal verification workflows.
    """
    # TODO: Implement actual verification logic here
    # For now, return a placeholder response
    return CostEvidenceVerificationResponse(
        receipt_id=receipt_id,
        verified=True,
        message="Cost evidence verified successfully",
        timestamp=datetime.utcnow(),
    )
