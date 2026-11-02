"""Initialization for default packet templates (ROP-06)."""

from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.db.models import PacketTemplate


async def save_default_templates(db: Session) -> int:
    """Save default packet templates for ROP-06."""
    defaults = [
        {
            "name": "Crypto News Aggregator",
            "slug": "crypto-news-aggregator",
            "description": "Default template for crypto news aggregation packets.",
            "source_categories": ["news", "social", "official"],
            "max_sources_per_packet": 10,
            "max_snapshots_per_source": 20,
            "max_claims_per_source": 50,
            "check_cooldown_seconds": 60,
            "retention_days": 30,
            "packet_structure": {
                "title": {"type": "string", "required": True},
                "summary": {"type": "string", "required": False},
                "sources": {"type": "array", "required": True},
            },
            "languages": "en",
            "status": "active",
        },
        {
            "name": "General Research Packet",
            "slug": "general-research-packet",
            "description": "Generic template for general research packets.",
            "source_categories": ["news", "social", "official", "academic"],
            "max_sources_per_packet": 10,
            "max_snapshots_per_source": 20,
            "max_claims_per_source": 50,
            "check_cooldown_seconds": 60,
            "retention_days": 30,
            "packet_structure": {
                "title": {"type": "string", "required": True},
                "summary": {"type": "string", "required": False},
                "sources": {"type": "array", "required": True},
            },
            "languages": "en",
            "status": "active",
        },
    ]

    inserted = 0
    for data in defaults:
        # Check if template with this slug already exists
        existing = db.query(PacketTemplate).filter(
            PacketTemplate.slug == data["slug"]
        ).first()
        if not existing:
            template = PacketTemplate(
                id=uuid4(),
                owner_user_id=None,  # System template
                name=data["name"],
                slug=data["slug"],
                description=data["description"],
                source_categories=data["source_categories"],
                max_sources_per_packet=data["max_sources_per_packet"],
                max_snapshots_per_source=data["max_snapshots_per_source"],
                max_claims_per_source=data["max_claims_per_source"],
                check_cooldown_seconds=data["check_cooldown_seconds"],
                retention_days=data["retention_days"],
                packet_structure=data["packet_structure"],
                languages=data["languages"],
                status=data["status"],
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(template)
            inserted += 1

    await db.flush()
    return inserted
