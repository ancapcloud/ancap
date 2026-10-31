"""Quality fixtures service for ROP-03 evaluation samples."""

from pathlib import Path
import json
from typing import Optional, List
from sqlalchemy import select
from app.db.models import QualityFixture
from app.schemas.quality_fixtures import QualityFixtureCreate, QualityFixtureResponse


def load_fixtures_from_file(file_path: str) -> List[dict]:
    """Load fixtures from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def create_quality_fixtures_batch(db, fixtures_data: List[dict]) -> List[QualityFixture]:
    """Batch create quality fixtures from loaded data."""
    created = []
    for fixture_data in fixtures_data:
        fixture = QualityFixture(
            fixture_type=fixture_data["fixture_type"],
            language=fixture_data["language"],
            sample_id=fixture_data["sample_id"],
            expected_result=fixture_data["expected_result"],
            actual_result=fixture_data.get("actual_result"),
            confidence_score=fixture_data.get("confidence_score"),
            is_available=fixture_data.get("is_available", True),
        )
        db.add(fixture)
        created.append(fixture)
    await db.commit()
    return created


async def get_quality_fixture(db, fixture_id: str) -> Optional[QualityFixture]:
    """Get a single quality fixture by ID."""
    result = await db.execute(select(QualityFixture).where(QualityFixture.id == fixture_id))
    return result.scalar_one_or_none()


async def get_all_quality_fixtures(db, limit: int = 100, offset: int = 0) -> List[QualityFixture]:
    """Paginated list of all quality fixtures."""
    result = await db.execute(
        select(QualityFixture)
        .order_by(QualityFixture.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_quality_fixtures_by_type(db, fixture_type: str, limit: int = 100) -> List[QualityFixture]:
    """Get fixtures filtered by type."""
    result = await db.execute(
        select(QualityFixture)
        .where(QualityFixture.fixture_type == fixture_type)
        .order_by(QualityFixture.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
