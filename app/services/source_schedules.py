"""Service layer for source schedules (ROP-03)."""

from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.db.models import SourceSchedule


def create_schedule(
    db: Session,
    project_id: str,
    source_type: str,
    source_pattern: Optional[str] = None,
    check_interval_minutes: int = 60,
    retention_days: int = 30,
    max_sources: int = 10,
    max_snapshots_per_source: int = 20,
    max_claims_per_source: int = 50,
    check_cooldown_seconds: int = 60,
    enabled: bool = True,
) -> SourceSchedule:
    """Create a new source schedule."""
    schedule = SourceSchedule(
        id=uuid.uuid4(),
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
    )
    db.add(schedule)
    db.flush()  # Don't commit yet
    return schedule


def get_schedule(db: Session, schedule_id: str) -> Optional[SourceSchedule]:
    """Get a schedule by ID."""
    return db.query(SourceSchedule).filter(SourceSchedule.id == schedule_id).first()


def list_schedules(
    db: Session,
    project_id: Optional[str] = None,
    source_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[List[SourceSchedule], int]:
    """List schedules with optional filters."""
    query = db.query(SourceSchedule)
    
    if project_id:
        query = query.filter(SourceSchedule.project_id == project_id)
    if source_type:
        query = query.filter(SourceSchedule.source_type == source_type)
    if enabled is not None:
        query = query.filter(SourceSchedule.enabled == enabled)
    
    schedules, total = query.order_by(SourceSchedule.created_at.desc()).offset(offset).limit(limit).all()
    total_query = db.query(SourceSchedule).filter(
        (SourceSchedule.project_id == project_id) if project_id else True,
        (SourceSchedule.source_type == source_type) if source_type else True,
        (SourceSchedule.enabled == enabled) if enabled is not None else True,
    )
    
    return schedules, total_query.count()


def delete_schedule(db: Session, schedule_id: str) -> bool:
    """Delete a schedule by ID."""
    schedule = db.query(SourceSchedule).filter(SourceSchedule.id == schedule_id).first()
    if schedule:
        db.delete(schedule)
        db.flush()
        return True
    return False


def save_default_schedules(db: Session) -> None:
    """Save default schedules for common use cases."""
    # Crypto client monitoring schedule
    crypto_client_schedule = SourceSchedule(
        id=uuid.uuid4(),
        project_id="default",
        source_type="crypto-client",
        source_pattern=r"^(https?://)?(?:www\.)?(?:etherscan|blockscout)\.io/.*$",
        check_interval_minutes=60,
        retention_days=30,
        max_sources=10,
        max_snapshots_per_source=20,
        max_claims_per_source=50,
        check_cooldown_seconds=60,
        enabled=True,
    )
    db.add(crypto_client_schedule)
    
    # Competitor analysis schedule
    competitor_schedule = SourceSchedule(
        id=uuid.uuid4(),
        project_id="default",
        source_type="competitor",
        source_pattern=r"^(https?://)?(?:www\.)?(?:ancap|blockscout)\.cloud/.*$",
        check_interval_minutes=30,
        retention_days=60,
        max_sources=5,
        max_snapshots_per_source=15,
        max_claims_per_source=30,
        check_cooldown_seconds=30,
        enabled=True,
    )
    db.add(competitor_schedule)
    
    # News aggregation schedule
    news_schedule = SourceSchedule(
        id=uuid.uuid4(),
        project_id="default",
        source_type="news",
        source_pattern=r"^(https?://)?(?:www\.)?(?:coindesk|cointelegraph|decrypt)\.com/.*$",
        check_interval_minutes=120,
        retention_days=45,
        max_sources=8,
        max_snapshots_per_source=25,
        max_claims_per_source=40,
        check_cooldown_seconds=60,
        enabled=True,
    )
    db.add(news_schedule)
    
    db.flush()
