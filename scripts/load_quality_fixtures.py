#!/usr/bin/env python3
"""Load initial quality fixtures from JSON into database."""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db_url
from app.db.models import QualityFixture
from scripts.generate_quality_fixtures import load_fixtures_from_file


def main():
    """Load fixtures from JSON file into database."""
    # Get database URL from environment or default
    db_url = os.environ.get("TEST_DATABASE_URL", get_db_url())
    
    print(f"Using database: {db_url}")
    
    # Create engine and session
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        # Load fixtures from JSON file
        fixtures_file = os.path.join(os.path.dirname(__file__), "quality_fixtures_initial.json")
        if not os.path.exists(fixtures_file):
            print(f"Fixtures file not found: {fixtures_file}")
            return
        
        fixtures_data = load_fixtures_from_file(fixtures_file)
        print(f"Loaded {len(fixtures_data)} fixtures from JSON")
        
        # Check if table exists, create if needed
        try:
            Base.metadata.create_all(bind=engine)
            print("Created quality_fixtures table")
        except Exception as e:
            print(f"Table already exists or error creating: {e}")
        
        # Batch insert fixtures
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
            session.add(fixture)
            created.append(fixture)
        
        session.commit()
        print(f"Created {len(created)} quality fixtures in database")
        print("Load complete!")


if __name__ == "__main__":
    main()
