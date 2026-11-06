"""ROP-04 renewal events admin API tests."""

from uuid import uuid4

from app.config import get_settings


def _admin_headers(client, monkeypatch):
    registered = client.post(
        "/v1/auth/users",
        headers={"Authorization": ""},
        json={
            "email": f"renewal_{uuid4().hex}@test.com",
            "password": "password123",
            "display_name": "Renewal admin",
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


def _payload(project_id: str, **overrides):
    body = {
        "project_id": project_id,
        "client_id": "client-a",
        "subscription_id": "sub-1",
        "renewal_type": "monthly",
        "due_at": "2026-12-01T00:00:00+00:00",
        "amount_due": "1250.50",
        "currency": "eur",
    }
    body.update(overrides)
    return body


def test_renewal_routes_are_canonical():
    from app.main import app

    paths = [getattr(r, "path", "") for r in app.routes if "renewal-events" in getattr(r, "path", "")]
    assert "/v1/renewal-events" in paths
    assert "/v1/renewal-events/cohort" in paths
    assert not any(p.startswith("/v1/v1/") for p in paths)


def test_renewal_events_require_platform_admin(client, monkeypatch):
    _admin_headers(client, monkeypatch)
    project = f"rop04-{uuid4().hex[:8]}"
    assert client.post("/v1/renewal-events", json=_payload(project), headers={"Authorization": ""}).status_code == 401
    assert client.post("/v1/renewal-events", json=_payload(project)).status_code == 403
    assert client.get("/v1/renewal-events").status_code == 403


def test_renewal_lifecycle_and_cohort(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    project = f"rop04-{uuid4().hex[:8]}"

    created = client.post("/v1/renewal-events", json=_payload(project), headers=headers)
    assert created.status_code == 201, created.text
    event = created.json()
    assert event["status"] == "pending"
    assert event["amount_due"] == "1250.5"
    assert event["currency"] == "EUR"
    assert created.headers["cache-control"] == "private, no-store"

    duplicate = client.post("/v1/renewal-events", json=_payload(project), headers=headers)
    assert duplicate.status_code == 409

    second = client.post(
        "/v1/renewal-events",
        json=_payload(project, client_id="client-b", amount_due="100", due_at="2026-12-05T00:00:00+00:00"),
        headers=headers,
    ).json()
    third = client.post(
        "/v1/renewal-events",
        json=_payload(project, client_id="client-c", amount_due="0.000000000000000001"),
        headers=headers,
    ).json()

    paid = client.post(
        f"/v1/renewal-events/{event['id']}/status",
        json={"status": "paid", "payment_reference": "invoice-42"},
        headers=headers,
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["renewed_at"] is not None
    # Idempotent repeat of the same final state.
    assert client.post(
        f"/v1/renewal-events/{event['id']}/status", json={"status": "paid"}, headers=headers
    ).status_code == 200
    # Terminal state cannot be reopened.
    assert client.post(
        f"/v1/renewal-events/{event['id']}/status", json={"status": "failed"}, headers=headers
    ).status_code == 409

    assert client.post(
        f"/v1/renewal-events/{second['id']}/status", json={"status": "failed"}, headers=headers
    ).status_code == 200

    cohort = client.get(
        "/v1/renewal-events/cohort",
        params={"project_id": project, "due_from": "2026-12-01T00:00:00Z", "due_to": "2027-01-01T00:00:00Z"},
        headers=headers,
    )
    assert cohort.status_code == 200, cohort.text
    data = cohort.json()
    assert (data["total"], data["paid"], data["failed"], data["pending"]) == (3, 1, 1, 1)
    assert data["renewal_rate"] == "0.5000"
    assert data["totals"] == [
        {"currency": "EUR", "due": "1350.500000000000000001", "paid": "1250.5"}
    ]

    listed = client.get("/v1/renewal-events", params={"project_id": project, "status": "pending"}, headers=headers)
    assert listed.status_code == 200
    assert [e["id"] for e in listed.json()["events"]] == [third["id"]]


def test_renewal_validation(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    project = f"rop04-{uuid4().hex[:8]}"
    assert client.post("/v1/renewal-events", json=_payload(project, amount_due="-1"), headers=headers).status_code == 422
    assert client.post(
        "/v1/renewal-events", json=_payload(project, due_at="2026-12-01T00:00:00"), headers=headers
    ).status_code == 422
    assert client.post(
        "/v1/renewal-events", json=_payload(project, renewal_type="weekly"), headers=headers
    ).status_code == 422
    assert client.get("/v1/renewal-events/not-a-uuid", headers=headers).status_code == 404
    assert client.get(
        "/v1/renewal-events/cohort",
        params={"due_from": "2027-01-01T00:00:00Z", "due_to": "2026-01-01T00:00:00Z"},
        headers=headers,
    ).status_code == 422


def test_renewal_duplicate_without_subscription_and_full_precision(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    project = f"rop04-{uuid4().hex[:8]}"
    amount = "12345678901.123456789012345678"
    body = _payload(project, subscription_id=None, amount_due=amount)

    first = client.post("/v1/renewal-events", json=body, headers=headers)
    assert first.status_code == 201, first.text
    assert first.json()["amount_due"] == amount
    # NULL subscription_id must not let retries inflate the cohort.
    assert client.post("/v1/renewal-events", json=body, headers=headers).status_code == 409

    client.post(
        "/v1/renewal-events",
        json=_payload(project, client_id="client-z", subscription_id=None, amount_due=amount),
        headers=headers,
    )
    cohort = client.get(
        "/v1/renewal-events/cohort",
        params={"project_id": project, "due_from": "2026-12-01T00:00:00Z", "due_to": "2026-12-02T00:00:00Z"},
        headers=headers,
    ).json()
    assert cohort["total"] == 2
    assert cohort["totals"][0]["due"] == "24691357802.246913578024691356"
