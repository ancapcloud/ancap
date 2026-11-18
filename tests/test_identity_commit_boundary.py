"""Identity success responses must follow commit, not race the next request."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import deps
from app.api.routers import agents, auth
from app.db.session import get_db


@pytest.mark.parametrize("path", ["/v1/agents", "/v1/auth/users"])
@pytest.mark.parametrize("commit_fails", [False, True])
def test_identity_is_committed_before_http_success(monkeypatch, path, commit_fails):
    events = []
    owner = str(uuid4())
    monkeypatch.setattr(deps, "decode_token", lambda _: owner)
    settings = SimpleNamespace(registration_max_agents_per_day=0, stake_to_activate_amount="0", access_token_expire_minutes=60)
    monkeypatch.setattr(agents, "get_settings", lambda: settings)
    monkeypatch.setattr(auth, "get_settings", lambda: settings)
    monkeypatch.setattr(auth, "_enforce_auth_rate_limit", AsyncMock())
    monkeypatch.setattr(auth, "verify_turnstile", AsyncMock())
    monkeypatch.setattr(auth, "hash_password", lambda _: "test-hash")
    monkeypatch.setattr(auth, "create_access_token", lambda _: "test-session-token")
    monkeypatch.setattr(auth, "create_wallet_for_user", AsyncMock(return_value=(None, None)))
    monkeypatch.setattr(auth, "evaluate_registration_signals", AsyncMock(return_value=SimpleNamespace(free_grants_allowed=False)))
    monkeypatch.setattr(auth, "issue_welcome_grant_idempotent", AsyncMock())

    class Session:
        def add(self, entity):
            self.entity = entity

        async def flush(self):
            self.entity.id = str(uuid4())
            self.entity.created_at = datetime.now(timezone.utc)

        async def refresh(self, _entity):
            pass

        async def execute(self, _query):
            return SimpleNamespace(scalar_one_or_none=lambda: None)

    async def database():
        session = Session()
        try:
            yield session
            if hasattr(session, "entity"):
                events.append("commit")
                if commit_fails:
                    raise RuntimeError("Test commit failure")
        finally:
            events.append("close")

    app = FastAPI()
    app.include_router(agents.router, prefix="/v1")
    app.include_router(auth.router, prefix="/v1")
    app.dependency_overrides[get_db] = database

    async def observed(scope, receive, send):
        async def record(message):
            if message["type"] == "http.response.start":
                events.append("response:" + str(message["status"]))
            await send(message)
        await app(scope, receive, record)

    body = ({"display_name": "Test agent", "public_key": "x" * 32, "roles": ["seller"]}
            if path.endswith("/agents") else {"email": "identity-test@example.com", "password": "test-password"})
    with TestClient(observed, raise_server_exceptions=False) as client:
        response = client.post(path, json=body, headers={"Authorization": "Bearer test-session-token"})
    assert response.status_code == (500 if commit_fails else 201), response.text
    sent = next(event for event in events if event.startswith("response:"))
    assert events.index("commit") < events.index(sent), events
    if commit_fails:
        assert "response:201" not in events
        assert "ancap_token" not in response.cookies
    elif path.endswith("/agents"):
        assert response.json()["owner_user_id"] == owner
