"""Router for source schedules (ROP-03)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.models import SourceSchedule
from app.services.source_schedules import create_schedule, get_schedule, list_schedules, delete_schedule
from app.schemas.source_schedules import (
    SourceScheduleCreate,
    SourceScheduleResponse,
    SourceScheduleListResponse,
)
from app.api.deps import DbSession, require_admin
from app.db.session import get_db
from app.api.deps import DbSession, require_admin


router = APIRouter(prefix="/v1/source-schedules", tags=["source-schedules"])


@router.post(
    "/{schedule_id}",
    response_model=SourceScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_schedule_endpoint(
    schedule_id: str,  # Ignored - using UUID for id field
    schedule_data: SourceScheduleCreate,
    db: Session = Depends(get_db),
):
    """Create a new source schedule."""
    # Generate a new UUID since the endpoint expects POST to create
    actual_schedule = create_schedule(
        db=db,
        project_id=schedule_data.project_id,
        source_type=schedule_data.source_type,
        source_pattern=schedule_data.source_pattern,
        check_interval_minutes=schedule_data.check_interval_minutes,
        retention_days=schedule_data.retention_days,
        max_sources=schedule_data.max_sources,
        max_snapshots_per_source=schedule_data.max_snapshots_per_source,
        max_claims_per_source=schedule_data.max_claims_per_source,
        check_cooldown_seconds=schedule_data.check_cooldown_seconds,
        enabled=schedule_data.enabled,
    )
    return actual_schedule


@router.get(
    "/{schedule_id}",
    response_model=SourceScheduleResponse,
    dependencies=[Depends(require_admin)],
)
async def get_schedule_endpoint(
    schedule_id: str,
    db: Session = Depends(get_db),
):
    """Get a schedule by ID."""
    schedule = get_schedule(db=db, schedule_id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source schedule {schedule_id} not found",
        )
    return schedule


@router.get(
    "/",
    response_model=SourceScheduleListResponse,
    dependencies=[Depends(require_admin)],
)
async def list_schedules_endpoint(
    project_id: Optional[str] = None,
    source_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List schedules with optional filters."""
    schedules, total = list_schedules(
        db=db,
        project_id=project_id,
        source_type=source_type,
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return SourceScheduleListResponse(
        schedules=schedules,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_schedule_endpoint(
    schedule_id: str,
    db: Session = Depends(get_db),
):
    """Delete a schedule by ID."""
    result = delete_schedule(db=db, schedule_id=schedule_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source schedule {schedule_id} not found",
        )
    return None
