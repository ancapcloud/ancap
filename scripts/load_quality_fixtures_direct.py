#!/usr/bin/env python3
"""Direct load quality fixtures for testing (no alembic)."""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import QualityFixture, Base
from app.config import get_settings


def main():
    """Load fixtures directly into test database."""
    settings = get_settings()
    
    # Use test database URL if available, otherwise use default
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    if not test_db_url:
        print("TEST_DATABASE_URL not set, using development database")
        test_db_url = str(settings.database_url)
    
    print(f"Using database: {test_db_url}")
    
    # Create engine and session
    engine = create_engine(test_db_url, echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    with SessionLocal() as session:
        # Load fixtures from JSON file
        fixtures_file = Path(__file__).parent / "quality_fixtures_initial.json"
        if not fixtures_file.exists():
            print(f"Fixtures file not found: {fixtures_file}")
            return
        
        import json
        with open(fixtures_file, "r", encoding="utf-8") as f:
            fixtures_data = json.load(f)
        
        print(f"Loaded {len(fixtures_data)} fixtures from JSON")
        
        # Batch insert fixtures
        created_count = 0
        for fixture_data in fixtures_data:
            try:
                fixture = QualityFixture(
                    fixture_type=fixture_data["fixture_type"],
                    language=fixture_data["language"],
                    sample_id=fixture_data["sample_id"],
                    expected_result=fixture_data["expected_result"],
                    actual_result=fixture_data.get("actual_result"),
                    confidence_score=fixture_data.get("confidence_score"),
                    is_available=fixture_data.get("is_available", True),
                )
                session.add(fixture)
                created_count += 1
            except Exception as e:
                print(f"Error creating fixture {fixture_data['sample_id']}: {e}")
        
        session.commit()
        print(f"Created {created_count} quality fixtures in database")
        print("Load complete!")


if __name__ == "__main__":
    main()
