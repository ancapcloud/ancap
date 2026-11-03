"""Service layer for source schedules (ROP-03)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SourceSchedule


async def create_schedule(
    session: AsyncSession,
    *,
    project_id: str,
    source_type: str,
    source_pattern: str | None = None,
    check_interval_minutes: int = 60,
    retention_days: int = 30,
    max_sources: int = 10,
    max_snapshots_per_source: int = 20,
    max_claims_per_source: int = 50,
    check_cooldown_seconds: int = 60,
    enabled: bool = True,
) -> SourceSchedule:
    now = datetime.now(timezone.utc)
    schedule = SourceSchedule(
        id=uuid4(),
        project_id=project_id,
        source_type=source_type,
        source_pattern=source_pattern,
        check_interval_minutes=check_interval_minutes,
        retention_days=retention_days,
        max_sources=max_sources,
        max_snapshots_per_source=max_snapshots_per_source,
        max_claims_per_source=max_claims_per_source,
        check_cooldown_seconds=check_cooldown_seconds,
        enabled=enabled,
        created_at=now,
        updated_at=now,
    )
    session.add(schedule)
    await session.flush()
    return schedule


async def get_schedule(session: AsyncSession, schedule_id: UUID) -> SourceSchedule | None:
    return (
        await session.execute(select(SourceSchedule).where(SourceSchedule.id == schedule_id))
    ).scalar_one_or_none()


async def list_schedules(
    session: AsyncSession,
    *,
    project_id: str | None = None,
    source_type: str | None = None,
    enabled: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[SourceSchedule], int]:
    filters = []
    if project_id is not None:
        filters.append(SourceSchedule.project_id == project_id)
    if source_type is not None:
        filters.append(SourceSchedule.source_type == source_type)
    if enabled is not None:
        filters.append(SourceSchedule.enabled == enabled)

    total = (
        await session.execute(select(func.count()).select_from(SourceSchedule).where(*filters))
    ).scalar_one()
    rows = (
        await session.execute(
            select(SourceSchedule)
            .where(*filters)
            .order_by(SourceSchedule.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return list(rows), int(total)


async def delete_schedule(session: AsyncSession, schedule_id: UUID) -> bool:
    schedule = await get_schedule(session, schedule_id)
    if schedule is None:
        return False
    await session.delete(schedule)
    await session.flush()
    return True
