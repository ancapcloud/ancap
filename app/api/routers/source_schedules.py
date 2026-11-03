"""Admin router for source schedules (ROP-03)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import DbSession, require_platform_admin
from app.schemas.source_schedules import (
    SourceScheduleCreate,
    SourceScheduleListResponse,
    SourceScheduleResponse,
)
from app.services import source_schedules as schedules_service

router = APIRouter(prefix="/source-schedules", tags=["source-schedules"])


def _public(row) -> SourceScheduleResponse:
    return SourceScheduleResponse.model_validate(
        {
            "id": str(row.id),
            "project_id": row.project_id,
            "source_type": row.source_type,
            "source_pattern": row.source_pattern,
            "check_interval_minutes": row.check_interval_minutes,
            "retention_days": row.retention_days,
            "max_sources": row.max_sources,
            "max_snapshots_per_source": row.max_snapshots_per_source,
            "max_claims_per_source": row.max_claims_per_source,
            "check_cooldown_seconds": row.check_cooldown_seconds,
            "enabled": row.enabled,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    )


@router.post(
    "",
    response_model=SourceScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    body: SourceScheduleCreate,
    session: DbSession,
    response: Response,
    _admin: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    row = await schedules_service.create_schedule(
        session,
        project_id=body.project_id,
        source_type=body.source_type,
        source_pattern=body.source_pattern,
        check_interval_minutes=body.check_interval_minutes,
        retention_days=body.retention_days,
        max_sources=body.max_sources,
        max_snapshots_per_source=body.max_snapshots_per_source,
        max_claims_per_source=body.max_claims_per_source,
        check_cooldown_seconds=body.check_cooldown_seconds,
        enabled=body.enabled,
    )
    return _public(row)


@router.get("", response_model=SourceScheduleListResponse)
async def list_schedules(
    session: DbSession,
    response: Response,
    project_id: str | None = None,
    source_type: str | None = None,
    enabled: bool | None = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _admin: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    rows, total = await schedules_service.list_schedules(
        session,
        project_id=project_id,
        source_type=source_type,
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return SourceScheduleListResponse(
        schedules=[_public(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{schedule_id}", response_model=SourceScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    session: DbSession,
    response: Response,
    _admin: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    row = await schedules_service.get_schedule(session, schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Source schedule not found")
    return _public(row)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    deleted = await schedules_service.delete_schedule(session, schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source schedule not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
