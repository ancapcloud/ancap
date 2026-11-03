"""Service layer for ROP-05 packet templates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.models import PacketTemplate


class DuplicateTemplateSlug(ValueError):
    """A reusable packet template already owns this slug."""


async def create_template(
    session: AsyncSession,
    *,
    name: str,
    slug: str,
    description: str | None = None,
    source_categories: list[str] | None = None,
    max_sources_per_packet: int = 10,
    max_snapshots_per_source: int = 20,
    max_claims_per_source: int = 50,
    check_cooldown_seconds: int = 60,
    retention_days: int = 30,
    packet_structure: dict[str, Any] | None = None,
    languages: str = "en",
    status: str = "draft",
    owner_user_id: UUID | None = None,
) -> PacketTemplate:
    now = datetime.now(timezone.utc)
    template = PacketTemplate(
        id=uuid4(),
        owner_user_id=owner_user_id,
        name=name,
        slug=slug,
        description=description,
        source_categories=list(source_categories or []),
        max_sources_per_packet=max_sources_per_packet,
        max_snapshots_per_source=max_snapshots_per_source,
        max_claims_per_source=max_claims_per_source,
        check_cooldown_seconds=check_cooldown_seconds,
        retention_days=retention_days,
        packet_structure=dict(packet_structure or {}),
        languages=languages,
        status=status,
        is_active=status == "active",
        created_at=now,
        updated_at=now,
    )
    try:
        async with session.begin_nested():
            session.add(template)
            await session.flush()
    except IntegrityError:
        existing = await session.scalar(select(PacketTemplate.id).where(PacketTemplate.slug == slug))
        if existing is not None:
            raise DuplicateTemplateSlug("Template slug already exists") from None
        raise
    return template


async def get_template(session: AsyncSession, template_id: UUID) -> PacketTemplate | None:
    result = await session.execute(select(PacketTemplate).where(PacketTemplate.id == template_id))
    return result.scalar_one_or_none()


async def list_templates(
    session: AsyncSession,
    *,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[PacketTemplate], int]:
    query = select(PacketTemplate)
    count_query = select(func.count()).select_from(PacketTemplate)
    if status is not None:
        query = query.where(PacketTemplate.status == status)
        count_query = count_query.where(PacketTemplate.status == status)
    result = await session.execute(
        query.order_by(PacketTemplate.created_at.desc()).offset(offset).limit(limit)
    )
    templates = list(result.scalars().all())
    total = int((await session.execute(count_query)).scalar_one())
    return templates, total


async def delete_template(session: AsyncSession, template_id: UUID) -> bool:
    template = await get_template(session, template_id)
    if not template:
        return False
    await session.delete(template)
    await session.flush()
    return True


async def save_default_templates(session: AsyncSession) -> int:
    """Insert reusable category/structure defaults; never client documents."""
    defaults = [
        {
            "name": "Crypto News Aggregator",
            "slug": "crypto-news-aggregator",
            "description": "Reusable categories/structure for crypto news packets.",
            "source_categories": ["news", "social", "official"],
            "packet_structure": {
                "title": {"type": "string", "required": True},
                "summary": {"type": "string", "required": False},
                "sources": {"type": "array", "required": True},
            },
            "status": "active",
        },
        {
            "name": "General Research Packet",
            "slug": "general-research-packet",
            "description": "Reusable categories/structure for general research packets.",
            "source_categories": ["news", "social", "official", "academic"],
            "packet_structure": {
                "title": {"type": "string", "required": True},
                "summary": {"type": "string", "required": False},
                "sources": {"type": "array", "required": True},
            },
            "status": "active",
        },
    ]
    inserted = 0
    for data in defaults:
        existing = await session.execute(
            select(PacketTemplate).where(PacketTemplate.slug == data["slug"])
        )
        if existing.scalar_one_or_none() is not None:
            continue
        await create_template(
            session,
            name=data["name"],
            slug=data["slug"],
            description=data["description"],
            source_categories=data["source_categories"],
            packet_structure=data["packet_structure"],
            status=data["status"],
        )
        inserted += 1
    return inserted
