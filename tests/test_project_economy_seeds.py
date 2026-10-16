"""Unit checks for People + AI project economy platform seeds (no DB)."""

from app.db.models import EconomyProject
from app.services.project_economy import (
    PLATFORM_SEED_PROJECTS,
    SEED_OWNER_DISPLAY_NAME,
    SEED_OWNER_EMAIL,
    _owner_display_name,
    project_to_public,
)


def test_platform_seeds_are_five_ai_demos_in_order():
    keys = [item["seed_key"] for item in PLATFORM_SEED_PROJECTS]
    assert keys == ["aeterna", "galaxy", "lunar", "stardust", "starlink"]
    assert len({item["slug"] for item in PLATFORM_SEED_PROJECTS}) == 5
    assert len({item["id"] for item in PLATFORM_SEED_PROJECTS}) == 5
    for item in PLATFORM_SEED_PROJECTS:
        assert item["background_href"].startswith("/")
        assert item["task_title"]
        assert item["acceptance_criteria"]
        assert item["kind"] in {"demo", "concept"}


def test_seed_owner_public_identity_hides_email():
    assert SEED_OWNER_DISPLAY_NAME == "3n3rgy"
    assert SEED_OWNER_EMAIL == "dragon.cat.trx@gmail.com"
    assert "@" not in SEED_OWNER_DISPLAY_NAME

    project = EconomyProject(
        id="11111111-1111-4111-8111-111111111101",
        owner_user_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        slug="aeterna-longevity-brief",
        title="AETERNA — longevity research brief",
        summary="summary",
        result_promise="result",
        status="published",
        kind="demo",
        seed_key="aeterna",
        is_platform_seed=True,
        background_href="/aeterna",
        metadata_json={},
        tasks=[],
    )
    assert _owner_display_name(project) == "3n3rgy"
    payload = project_to_public(project)
    assert payload["owner_display_name"] == "3n3rgy"
    assert SEED_OWNER_EMAIL not in str(payload)


def test_ff_project_economy_defaults_false():
    from app.config import Settings

    assert Settings().ff_project_economy is False
