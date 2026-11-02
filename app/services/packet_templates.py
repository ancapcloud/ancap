"""Service layer for packet templates (ROP-06)."""

from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.models import PacketTemplate


class PacketTemplatesService:
    """Service for managing packet templates."""

    @staticmethod
    async def create_template(
        db: Session,
        owner_user_id: Optional[UUID],
        name: str,
        slug: str,
        description: Optional[str] = None,
        source_categories: Optional[List[str]] = None,
        max_sources_per_packet: int = 10,
        max_snapshots_per_source: int = 20,
        max_claims_per_source: int = 50,
        check_cooldown_seconds: int = 60,
        retention_days: int = 30,
        packet_structure: Optional[Dict[str, Any]] = None,
        languages: str = "en",
        status: str = "draft",
    ) -> PacketTemplate:
        """Create a new packet template."""
        if source_categories is None:
            source_categories = []
        if packet_structure is None:
            packet_structure = {}

        template = PacketTemplate(
            owner_user_id=owner_user_id,
            name=name,
            slug=slug,
            description=description,
            source_categories=source_categories,
            max_sources_per_packet=max_sources_per_packet,
            max_snapshots_per_source=max_snapshots_per_source,
            max_claims_per_source=max_claims_per_source,
            check_cooldown_seconds=check_cooldown_seconds,
            retention_days=retention_days,
            packet_structure=packet_structure,
            languages=languages,
            status=status,
        )

        db.add(template)
        await db.flush()
        return template

    @staticmethod
    async def get_template(db: Session, template_id: UUID) -> Optional[PacketTemplate]:
        """Get a packet template by ID."""
        stmt = select(PacketTemplate).where(PacketTemplate.id == template_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_templates(
        db: Session,
        owner_user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[PacketTemplate], int]:
        """List packet templates with optional filtering."""
        stmt = select(PacketTemplate)
        if owner_user_id is not None:
            stmt = stmt.where(PacketTemplate.owner_user_id == owner_user_id)
        if status is not None:
            stmt = stmt.where(PacketTemplate.status == status)

        stmt = stmt.order_by(PacketTemplate.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await db.execute(stmt)
        templates = result.scalars().all()

        total_stmt = select(func.count()).select_from(PacketTemplate)
        if owner_user_id is not None:
            total_stmt = total_stmt.where(PacketTemplate.owner_user_id == owner_user_id)
        if status is not None:
            total_stmt = total_stmt.where(PacketTemplate.status == status)

        total_result = await db.execute(total_stmt)
        total = total_result.scalar()

        return templates, total

    @staticmethod
    async def delete_template(db: Session, template_id: UUID) -> bool:
        """Delete a packet template."""
        template = await db.get(PacketTemplate, template_id)
        if template:
            db.delete(template)
            await db.flush()
            return True
        return False
