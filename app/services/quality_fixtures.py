"""Quality fixtures service for ROP-03 evaluation samples."""

from pathlib import Path
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import QualityFixture
from app.schemas.quality_fixtures import QualityFixtureCreate, QualityFixtureResponse


def load_fixtures_from_file(file_path: str) -> List[dict]:
    """Load fixtures from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_quality_fixtures_batch(db: Session, fixtures_data: List[dict]) -> List[QualityFixture]:
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
    db.commit()
    return created


def get_quality_fixture(db: Session, fixture_id: str) -> Optional[QualityFixture]:
    """Get a single quality fixture by ID."""
    return db.query(QualityFixture).filter(QualityFixture.id == fixture_id).first()


def get_all_quality_fixtures(db: Session, limit: int = 100, offset: int = 0) -> List[QualityFixture]:
    """Paginated list of all quality fixtures."""
    return db.query(QualityFixture).order_by(QualityFixture.created_at.desc()).limit(limit).offset(offset).all()


def get_quality_fixtures_by_type(db: Session, fixture_type: str, limit: int = 100) -> List[QualityFixture]:
    """Get fixtures filtered by type."""
    return db.query(QualityFixture).filter(
        QualityFixture.fixture_type == fixture_type
    ).order_by(QualityFixture.created_at.desc()).limit(limit).all()
