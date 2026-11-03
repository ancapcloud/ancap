"""ROP-05 packet template admin API tests (behavior from Theodore 8a42905f/b1440775, cleaned)."""

from uuid import uuid4

from app.config import get_settings


def _admin_headers(client, monkeypatch):
    registered = client.post(
        "/v1/auth/users",
        headers={"Authorization": ""},
        json={
            "email": f"packet_{uuid4().hex}@test.com",
            "password": "password123",
            "display_name": "Packet admin",
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


def test_packet_template_routes_are_canonical_and_unique():
    from app.main import app

    paths = [
        getattr(route, "path", "")
        for route in app.routes
        if "packet-template" in getattr(route, "path", "")
    ]
    assert paths, "packet-templates router must be mounted"
    assert not any(path.startswith("/v1/v1/") for path in paths)
    get_paths = [
        getattr(route, "path", "")
        for route in app.routes
        if getattr(route, "path", "").endswith("/packet-templates/{template_id}")
        and "GET" in getattr(route, "methods", set())
    ]
    assert len(get_paths) == 1


def test_packet_templates_admin_crud_and_auth(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    payload = {
        "name": "Pilot Packet",
        "slug": f"pilot-packet-{uuid4().hex[:8]}",
        "description": "Reusable categories only",
        "source_categories": ["news", "official"],
        "max_sources_per_packet": 10,
        "max_snapshots_per_source": 20,
        "max_claims_per_source": 50,
        "check_cooldown_seconds": 60,
        "retention_days": 30,
        "packet_structure": {"title": {"type": "string", "required": True}},
        "languages": "en",
        "status": "active",
    }

    assert client.post("/v1/packet-templates", json=payload, headers={"Authorization": ""}).status_code == 401
    assert client.post("/v1/packet-templates", json=payload).status_code == 403

    created = client.post("/v1/packet-templates", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    assert created.headers["cache-control"] == "private, no-store"
    body = created.json()
    template_id = body["id"]
    assert body["slug"] == payload["slug"]
    assert body["source_categories"] == ["news", "official"]
    assert body["is_active"] is True

    duplicate = client.post("/v1/packet-templates", json=payload, headers=headers)
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.headers["cache-control"] == "private, no-store"
    retry_payload = {**payload, "slug": f"retry-{uuid4().hex[:8]}"}
    retry = client.post("/v1/packet-templates", json=retry_payload, headers=headers)
    assert retry.status_code == 201, retry.text

    listed = client.get("/v1/packet-templates?status=active", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] >= 1
    assert any(item["id"] == template_id for item in listed.json()["templates"])

    fetched = client.get(f"/v1/packet-templates/{template_id}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    assert fetched.headers["cache-control"] == "private, no-store"
    assert fetched.json()["name"] == "Pilot Packet"

    assert client.get(f"/v1/packet-templates/{uuid4()}", headers=headers).status_code == 404
    deleted = client.delete(f"/v1/packet-templates/{template_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/v1/packet-templates/{template_id}", headers=headers).status_code == 404
