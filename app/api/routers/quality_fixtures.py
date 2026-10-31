"""Admin-only router for quality fixtures (ROP-03)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services.quality_fixtures import (
    get_quality_fixture,
    get_all_quality_fixtures,
)
from app.schemas.quality_fixtures import QualityFixtureResponse, QualityFixtureListResponse
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/v1/quality-fixtures", tags=["quality-fixtures-admin"])


@router.get(
    "/{fixture_id}",
    response_model=QualityFixtureResponse,
    dependencies=[Depends(require_admin)],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "Fixture not found"},
    },
)
async def get_quality_fixture_admin(
    fixture_id: str,
    db: Session = Depends(get_db),
):
    """
    Admin-only GET /v1/quality-fixtures/{id} for quality fixture retrieval.
    
    Returns full fixture record with allocations and metadata.
    Cache-Control: private, no-store; guest 401, user 403, unknown ID 404.
    verification_basis=operator_attested.
    """
    fixture = get_quality_fixture(db, fixture_id)
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quality fixture {fixture_id} not found",
        )
    return fixture


@router.get(
    "/",
    response_model=QualityFixtureListResponse,
    dependencies=[Depends(require_admin)],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
async def list_quality_fixtures(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Admin-only list all quality fixtures.
    
    Returns paginated list of fixtures with metadata.
    Cache-Control: private, no-store; guest 401, user 403.
    """
    fixtures, total = get_all_quality_fixtures(db, limit=limit, offset=offset)
    return QualityFixtureListResponse(
        fixtures=fixtures,
        total=total,
        limit=limit,
        offset=offset,
    )
