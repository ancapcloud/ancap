"""API smoke for project economy — requires disposable TEST_DATABASE_URL.

Skip when TEST_DATABASE_URL is unset so local/default `ancap` DB is never used
via this module's client fixture path.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not (os.environ.get("TEST_DATABASE_URL") or "").strip(),
    reason="Set TEST_DATABASE_URL to a disposable PostgreSQL DB before running",
)


def test_list_returns_five_platform_seeds(client):
    response = client.get("/v1/economy/projects", headers={"Authorization": ""})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 5
    assert payload["preview_only"] is True
    assert payload["mutations_enabled"] is False
    seeds = [item for item in payload["items"] if item.get("is_platform_seed")]
    assert len(seeds) >= 5
    keys = {item["seed_key"] for item in seeds}
    assert {"aeterna", "galaxy", "lunar", "stardust", "starlink"}.issubset(keys)


def test_get_seed_by_slug(client):
    response = client.get("/v1/economy/projects/aeterna-longevity-brief", headers={"Authorization": ""})
    assert response.status_code == 200
    body = response.json()
    assert body["seed_key"] == "aeterna"
    assert body["is_platform_seed"] is True
    assert body["status"] == "published"
    assert len(body["tasks"]) >= 1
    assert body["owner_display_name"] == "3n3rgy"
    assert body.get("owner_user_id")
    blob = str(body).lower()
    assert "dragon.cat.trx@gmail.com" not in blob
    assert "@" not in (body.get("owner_display_name") or "")


def test_create_blocked_when_flag_off(client):
    response = client.post(
        "/v1/economy/projects",
        json={
            "slug": "should-not-create",
            "title": "Blocked",
            "summary": "x",
            "result_promise": "y",
            "tasks": [{"title": "t", "acceptance_criteria": "c"}],
        },
    )
    assert response.status_code == 403
