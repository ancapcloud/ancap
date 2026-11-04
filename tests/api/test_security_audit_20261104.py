"""Regression tests for the 2026-11-04 security audit.

Each test pins one finding: anonymous or cross-account writes that used to
succeed, and the case-variant e-mail admin escalation.
"""
import uuid

import pytest

from app.config import get_settings
from tests.conftest import unique_name

ANON = {"Authorization": ""}


def _register(client, email: str | None = None):
    email = email or f"audit_{uuid.uuid4().hex[:10]}@example.com"
    r = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "audit"},
        headers=ANON,
    )
    return r


def _user_headers(client):
    r = _register(client)
    assert r.status_code in (200, 201), r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _agent(client, headers=None):
    r = client.post(
        "/v1/agents",
        json={"display_name": unique_name("audit_agent"), "public_key": "a" * 32, "roles": ["seller"]},
        headers=headers or {},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.mark.parametrize(
    "path,body",
    [
        ("/v1/risk/kill", {"scope_type": "pool", "scope_id": str(uuid.uuid4())}),
        ("/v1/risk/limits", {"scope_type": "pool", "scope_id": str(uuid.uuid4()), "policy_json": {"max_loss_pct": 1}}),
        ("/v1/pools", {"name": "anon-pool", "risk_profile": "low"}),
    ],
)
def test_anonymous_writes_are_rejected(client, path, body):
    r = client.post(path, json=body, headers=ANON)
    assert r.status_code == 401, r.text


def test_risk_controls_require_platform_admin(client, monkeypatch):
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "00000000-0000-0000-0000-000000000001")
    get_settings.cache_clear()
    try:
        headers = _user_headers(client)
        for path, body in (
            ("/v1/risk/kill", {"scope_type": "pool", "scope_id": str(uuid.uuid4())}),
            ("/v1/risk/limits", {"scope_type": "pool", "scope_id": str(uuid.uuid4()), "policy_json": {}}),
            (f"/v1/verticals/{uuid.uuid4()}/review", {"decision": "approve"}),
            (f"/v1/disputes/{uuid.uuid4()}/verdict", {"verdict": "resolved"}),
            ("/v1/reviews/ai", {"target_type": "listing", "target_id": str(uuid.uuid4()), "rating": 5}),
        ):
            r = client.post(path, json=body, headers=headers)
            assert r.status_code in (403, 422), (path, r.status_code, r.text)
            if r.status_code == 403:
                assert r.json()["detail"] == "Platform admin required"
    finally:
        get_settings.cache_clear()


def test_cannot_publish_version_into_someone_elses_strategy(client, base_vertical_id):
    owner_agent = _agent(client)  # owned by the default test user
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("audit_strat"), "vertical_id": base_vertical_id, "owner_agent_id": owner_agent},
    )
    assert strat.status_code == 201, strat.text
    sid = strat.json()["id"]

    intruder = _user_headers(client)
    r = client.post(
        f"/v1/strategies/{sid}/versions",
        json={
            "semver": "9.9.9",
            "workflow": {
                "vertical_id": base_vertical_id,
                "version": "1.0",
                "steps": [{"id": "s1", "action": "const", "args": {"value": 1}}],
            },
        },
        headers=intruder,
    )
    assert r.status_code == 403, r.text

    # The owner can still publish.
    ok = client.post(
        f"/v1/strategies/{sid}/versions",
        json={
            "semver": "1.0.0",
            "workflow": {
                "vertical_id": base_vertical_id,
                "version": "1.0",
                "steps": [{"id": "s1", "action": "const", "args": {"value": 1}}],
            },
        },
    )
    assert ok.status_code == 201, ok.text


def test_cannot_create_strategy_for_foreign_agent(client, base_vertical_id):
    victim_agent = _agent(client)
    intruder = _user_headers(client)
    r = client.post(
        "/v1/strategies",
        json={"name": unique_name("hijack"), "vertical_id": base_vertical_id, "owner_agent_id": victim_agent},
        headers=intruder,
    )
    assert r.status_code == 403, r.text


def test_review_cannot_impersonate_another_reviewer(client):
    victim_agent = _agent(client)
    intruder = _user_headers(client)
    target = str(uuid.uuid4())
    for reviewer_type, reviewer_id in (("agent", victim_agent), ("user", str(uuid.uuid4())), ("ai", str(uuid.uuid4()))):
        r = client.post(
            "/v1/reviews",
            json={
                "reviewer_type": reviewer_type,
                "reviewer_id": reviewer_id,
                "target_type": "listing",
                "target_id": target,
                "weight": 1.0,
            },
            headers=intruder,
        )
        assert r.status_code == 403, (reviewer_type, r.text)


def test_agent_create_ignores_foreign_owner_user_id(client):
    victim_user_id = str(uuid.uuid4())
    r = client.post(
        "/v1/agents",
        json={
            "display_name": unique_name("anon_agent"),
            "public_key": "b" * 32,
            "roles": ["seller"],
            "owner_user_id": victim_user_id,
        },
        headers=ANON,
    )
    if r.status_code == 201:
        assert r.json().get("owner_user_id") != victim_user_id


def test_case_variant_email_cannot_become_platform_admin(client, monkeypatch):
    base = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    first = _register(client, base)
    assert first.status_code in (200, 201), first.text

    # The same mailbox in different casing must not create a second account.
    dup = _register(client, base.upper().replace("@EXAMPLE.COM", "@example.com"))
    assert dup.status_code == 400, dup.text

    # And login still works regardless of how the user types the address.
    login = client.post(
        "/v1/auth/login",
        json={"email": base.upper().replace("@EXAMPLE.COM", "@example.com"), "password": "password123"},
        headers=ANON,
    )
    assert login.status_code == 200, login.text

    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", base)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
    get_settings.cache_clear()
    try:
        token = login.json()["access_token"]
        ok = client.post(
            "/v1/risk/kill",
            json={"scope_type": "pool", "scope_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ok.status_code == 200, ok.text
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_admin_email_requires_exact_stored_address(monkeypatch):
    """A legacy mixed-case duplicate account must not match the admin allowlist."""
    from app.api import deps

    class _Result:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

        def scalar_one(self):
            return self._value

    class _Session:
        def __init__(self, email, dupes):
            self.calls = [email, dupes]

        async def execute(self, _stmt):
            return _Result(self.calls.pop(0))

    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "boss@example.com")
    get_settings.cache_clear()
    try:
        assert await deps.is_platform_admin_user(_Session("BOSS@example.com", 2), str(uuid.uuid4())) is False
        assert await deps.is_platform_admin_user(_Session("boss@example.com", 2), str(uuid.uuid4())) is False
        assert await deps.is_platform_admin_user(_Session("boss@example.com", 1), str(uuid.uuid4())) is True
    finally:
        get_settings.cache_clear()


def test_scenario_flows_are_admin_only_and_off_in_production(client, monkeypatch):
    anon = client.post("/v1/flows/run", json={"flow_id": "flow1"}, headers=ANON)
    assert anon.status_code == 401, anon.text

    from types import SimpleNamespace

    from app.api.routers import flows as flows_router
    from app.services.auth import decode_token

    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", decode_token(client.default_token))
    get_settings.cache_clear()
    monkeypatch.setattr(flows_router, "get_settings", lambda: SimpleNamespace(environment="production"))
    try:
        prod = client.post("/v1/flows/run", json={"flow_id": "flow1"})
        assert prod.status_code == 404, prod.text
    finally:
        get_settings.cache_clear()
