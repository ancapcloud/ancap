"""Unit tests for quality fixtures service."""

from uuid import uuid4

import pytest
from app.services.quality_fixtures import (
    load_fixtures_from_file,
    create_quality_fixtures_batch,
    get_quality_fixture,
    get_all_quality_fixtures,
    get_quality_fixtures_by_type,
)


@pytest.mark.asyncio
async def test_load_fixtures_from_file(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.quality_fixtures.FIXTURES_ROOT", tmp_path)
    """Test loading fixtures from JSON file."""
    fixture_data = [
        {
            "fixture_type": "price_change",
            "language": "en",
            "sample_id": "test-001",
            "expected_result": "detected_price_increase",
            "confidence_score": 0.95,
        }
    ]
    file_path = tmp_path / "fixtures.json"
    import json
    with open(file_path, "w") as f:
        json.dump(fixture_data, f)

    loaded = load_fixtures_from_file(str(file_path))
    assert len(loaded) == 1
    assert loaded[0]["sample_id"] == "test-001"


@pytest.mark.asyncio
async def test_create_quality_fixtures_batch(db_session):
    """Test batch creation of quality fixtures."""
    fixture_data = [
        {
            "fixture_type": "price_change",
            "language": "en",
            "sample_id": "test-001",
            "expected_result": "detected_price_increase",
            "confidence_score": 0.95,
            "is_available": True,
        }
    ]
    created = await create_quality_fixtures_batch(db_session, fixture_data)
    assert len(created) == 1
    assert created[0].fixture_type == "price_change"
    assert created[0].sample_id == "test-001"


@pytest.mark.asyncio
async def test_get_quality_fixture(db_session):
    """Test retrieving a single fixture by ID."""
    # First create a fixture
    fixture_data = {
        "fixture_type": "price_change",
        "language": "en",
        "sample_id": "test-001",
        "expected_result": "detected_price_increase",
        "confidence_score": 0.95,
    }
    created = await create_quality_fixtures_batch(db_session, [fixture_data])
    fixture_id = str(created[0].id)

    # Now retrieve it
    retrieved = await get_quality_fixture(db_session, fixture_id)
    assert retrieved is not None
    assert retrieved.sample_id == "test-001"


@pytest.mark.asyncio
async def test_get_all_quality_fixtures(db_session):
    """Test paginated retrieval of all fixtures."""
    # Create multiple fixtures
    fixtures_data = [
        {
            "fixture_type": "price_change",
            "language": "en",
            "sample_id": f"test-{i:03d}",
            "expected_result": "detected_price_increase",
            "confidence_score": 0.95 - i * 0.01,
        }
        for i in range(5)
    ]
    await create_quality_fixtures_batch(db_session, fixtures_data)

    # Retrieve with pagination
    results, total = await get_all_quality_fixtures(db_session, limit=3, offset=0)
    assert len(results) == 3
    # Other tests may have committed fixtures already; only the page size is scoped here.
    assert total >= 5


@pytest.mark.asyncio
async def test_get_quality_fixtures_by_type(db_session):
    """Test filtering fixtures by type."""
    price_type = f"price_{uuid4().hex[:8]}"
    unavailable_type = f"unavail_{uuid4().hex[:8]}"
    # Create fixtures of different types
    fixtures_data = [
        {
            "fixture_type": price_type,
            "language": "en",
            "sample_id": f"pc-{i:03d}",
            "expected_result": "detected_price_increase",
        }
        for i in range(3)
    ] + [
        {
            "fixture_type": unavailable_type,
            "language": "en",
            "sample_id": f"us-{i:03d}",
            "expected_result": "source_unreachable_timeout",
        }
        for i in range(2)
    ]

    await create_quality_fixtures_batch(db_session, fixtures_data)

    # Filter by type
    price_fixtures = await get_quality_fixtures_by_type(db_session, price_type)
    unavailable_fixtures = await get_quality_fixtures_by_type(db_session, unavailable_type)

    assert len(price_fixtures) == 3
    assert len(unavailable_fixtures) == 2


@pytest.mark.asyncio
async def test_create_duplicate_sample_id_raises(db_session):
    """Test that duplicate sample IDs are rejected."""
    # Create first fixture
    fixture_data = {
        "fixture_type": "price_change",
        "language": "en",
        "sample_id": "duplicate-test",
        "expected_result": "detected_price_increase",
    }
    await create_quality_fixtures_batch(db_session, [fixture_data])

    # Try to create duplicate - should fail due to unique constraint on sample_id
    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        await create_quality_fixtures_batch(db_session, [fixture_data])


@pytest.mark.parametrize("path", ["../outside.json", "/etc/passwd", "fixture.txt"])
def test_load_fixture_rejects_unsafe_paths(tmp_path, monkeypatch, path):
    monkeypatch.setattr("app.services.quality_fixtures.FIXTURES_ROOT", tmp_path)
    with pytest.raises(ValueError, match="within the fixture directory"):
        load_fixtures_from_file(path)


def test_load_fixture_rejects_symlink_escape(tmp_path, monkeypatch):
    root = tmp_path / "fixtures"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("[]")
    try:
        (root / "link.json").symlink_to(outside)
    except OSError:
        pytest.skip("Creating symbolic links requires OS permission")
    monkeypatch.setattr("app.services.quality_fixtures.FIXTURES_ROOT", root)
    with pytest.raises(ValueError, match="within the fixture directory"):
        load_fixtures_from_file("link.json")
