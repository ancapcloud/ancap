"""ROP-03 source schedule admin API tests."""

from uuid import uuid4

from app.config import get_settings


def _admin_headers(client, monkeypatch):
    registered = client.post(
        "/v1/auth/users",
        headers={"Authorization": ""},
        json={
            "email": f"sched_{uuid4().hex}@test.com",
            "password": "password123",
            "display_name": "Schedule admin",
        },
    )
    assert registered.status_code in (200, 201), registered.text
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    user = client.get("/v1/users/me", headers=headers).json()["id"]
    monkeypatch.setattr(
        type(get_settings()),
        "platform_admin_user_ids_allowlist",
        property(lambda self: (user,)),
    )
    return headers


def test_source_schedule_routes_are_canonical():
    from app.main import app

    paths = sorted(
        getattr(route, "path", "")
        for route in app.routes
        if "source-schedule" in getattr(route, "path", "")
    )
    assert "/v1/v1/source-schedules" not in "".join(paths)
    assert any(path.startswith("/v1/source-schedules") for path in paths)


def test_source_schedules_admin_crud_and_auth(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    payload = {
        "project_id": "pilot-project",
        "source_type": "crypto-client",
        "source_pattern": "example.com/*",
        "check_interval_minutes": 60,
        "retention_days": 30,
        "max_sources": 10,
        "max_snapshots_per_source": 20,
        "max_claims_per_source": 50,
        "check_cooldown_seconds": 60,
        "enabled": True,
    }

    assert client.post("/v1/source-schedules", json=payload, headers={"Authorization": ""}).status_code == 401
    assert client.post("/v1/source-schedules", json=payload).status_code == 403

    created = client.post("/v1/source-schedules", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    assert created.headers["cache-control"] == "private, no-store"
    schedule_id = created.json()["id"]
    assert created.json()["project_id"] == "pilot-project"

    listed = client.get("/v1/source-schedules?project_id=pilot-project", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] >= 1
    assert any(item["id"] == schedule_id for item in listed.json()["schedules"])

    fetched = client.get(f"/v1/source-schedules/{schedule_id}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["source_type"] == "crypto-client"

    assert client.get(f"/v1/source-schedules/{uuid4()}", headers=headers).status_code == 404
    deleted = client.delete(f"/v1/source-schedules/{schedule_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/v1/source-schedules/{schedule_id}", headers=headers).status_code == 404
