"""Fixture loaders for quality evaluation samples."""

import json
from pathlib import Path
from typing import List, Dict, Any


def load_fixture_file(file_path: str) -> List[Dict[str, Any]]:
    """Load fixtures from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_fixture_files(directory: str = None) -> List[Dict[str, Any]]:
    """Load all fixture files from the fixtures directory."""
    base_dir = Path(__file__).parent.parent / "fixtures" if directory is None else Path(directory)
    all_fixtures: List[Dict[str, Any]] = []
    
    for json_file in base_dir.glob("*.json"):
        fixtures = load_fixture_file(str(json_file))
        all_fixtures.extend(fixtures)
    
    return all_fixtures


def create_fixture_batch(db_session, fixtures_data: List[Dict[str, Any]]) -> List[Any]:
    """Batch create quality fixtures from loaded data."""
    from app.services.quality_fixtures import create_quality_fixtures_batch
    return create_quality_fixtures_batch(db_session, fixtures_data)
