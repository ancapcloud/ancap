from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4


def account(client):
    response = client.post("/v1/auth/users", headers={"Authorization": ""}, json={
        "email": f"account_key_{uuid4().hex}@test.com", "password": "password123", "display_name": "API owner",
    })
    assert response.status_code in (200, 201), response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    profile = client.get("/v1/users/me", headers=headers).json()
    return profile, headers


def issue(client, headers):
    response = client.post("/v1/keys/account", headers=headers)
    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()["key"]


def key_headers(key):
    return {"Authorization": "", "X-API-Key": key}


def test_account_key_without_agent_selection_authenticates_owner_only(client):
    owner, headers = account(client)
    other, other_headers = account(client)
    key = issue(client, headers)
    assert client.post("/v1/keys/account", headers=headers).status_code == 409
    for auth in (key_headers(key), {"Authorization": f"Bearer {key}"}):
        me = client.get("/v1/users/me", headers=auth)
        assert me.status_code == 200, me.text
        assert me.json()["id"] == owner["id"]
    status = client.get("/v1/keys/account", headers=headers).json()
    assert status["active"] and "key" not in status
    assert key not in str(status)
    assert client.get("/v1/keys/account", headers=other_headers).json()["active"] is False
    assert client.get("/v1/users/me", headers={**other_headers, "X-API-Key": key}).status_code == 401
    other_agent = client.post("/v1/agents", headers=other_headers, json={
        "display_name": "Other agent", "public_key": "x" * 32, "roles": ["buyer"],
    }).json()["id"]
    assert client.post("/v1/keys", headers=key_headers(key), json={"agent_id": other_agent}).status_code == 403


def test_rotation_revocation_reissue_and_request_statistics(client):
    _, headers = account(client)
    old = issue(client, headers)
    assert client.get("/v1/users/me", headers=key_headers(old)).status_code == 200
    assert client.get("/v1/not-a-real-api-route", headers=key_headers(old)).status_code == 404
    stats = client.get("/v1/keys/account", headers=headers).json()
    assert stats["requests"] == 2
    assert stats["successful_requests"] == 1
    assert stats["failed_requests"] == 1
    assert stats["last_used_at"]
    rotation = client.post("/v1/keys/account/rotate", headers=headers)
    assert rotation.status_code == 200, rotation.text
    new = rotation.json()["key"]
    assert new != old and rotation.json()["requests"] == 2
    old_status = client.get("/v1/users/me", headers=key_headers(old)).status_code
    new_status = client.get("/v1/users/me", headers=key_headers(new)).status_code
    delete_status = client.delete("/v1/keys/account", headers=headers).status_code
    after_delete = client.get("/v1/users/me", headers=key_headers(new)).status_code
    assert old_status == 401
    assert new_status == 200
    assert delete_status == 204
    assert after_delete == 401
    revoked = client.get("/v1/keys/account", headers=headers).json()
    assert not revoked["active"] and revoked["requests"] == 3
    assert client.post("/v1/keys/account/rotate", headers=headers).status_code == 404
    reissued = issue(client, headers)
    assert client.get("/v1/users/me", headers=key_headers(reissued)).status_code == 200
    assert client.get("/v1/keys/account", headers=headers).json()["requests"] == 4


def test_invalid_and_legacy_keys_do_not_fall_back_to_cookie_or_gain_account_access(client):
    _, headers = account(client)
    agent = client.post("/v1/agents", headers=headers, json={
        "display_name": "Scoped legacy", "public_key": "a" * 32, "roles": ["buyer"],
    }).json()["id"]
    legacy = client.post("/v1/keys", headers=headers, json={"agent_id": agent}).json()["key"]
    assert client.get("/v1/users/me", headers={**headers, "X-API-Key": legacy}).status_code == 200
    for raw in ("ancap_invalid", legacy):
        auth = key_headers(raw)
        auth["Cookie"] = "ancap_token=" + headers["Authorization"][7:]
        assert client.get("/v1/users/me", headers=auth).status_code == 401
        assert client.post("/v1/keys/account", headers=auth).status_code == 401


def test_simultaneous_issuance_has_exactly_one_winner(client):
    _, headers = account(client)
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda _: client.post("/v1/keys/account", headers=headers).status_code, range(2)))
    assert sorted(results) == [201, 409]


def test_account_key_works_with_existing_paid_api_and_charges_owner(client):
    owner, headers = account(client)
    key = issue(client, headers)
    deposit = client.post("/v1/ledger/deposit", headers=headers, json={
        "account_owner_type": "user", "account_owner_id": owner["id"],
        "amount": {"amount": "10", "currency": "ACP"}, "reference": "account-key-test",
    })
    assert deposit.status_code == 201, deposit.text
    result = client.post("/v1/paid-api/token-risk", headers=key_headers(key), json={
        "subject": "TEST", "chain": "Base", "signals": {},
    })
    assert result.status_code == 200, result.text
    usage = client.get("/v1/paid-api/me/usage", headers=key_headers(key))
    assert usage.status_code == 200, usage.text
    assert len(usage.json()["items"]) == 1
    assert usage.json()["items"][0]["owner_user_id"] == owner["id"]


def test_expired_key_cannot_authenticate_and_self_revocation_works(client, db_cursor):
    _, headers = account(client)
    key = issue(client, headers)
    db_cursor.execute("UPDATE api_keys SET expires_at = NOW() - INTERVAL '1 minute' WHERE key_prefix = %s", (key[:18],))
    db_cursor.connection.commit()
    expired_status = client.get("/v1/users/me", headers=key_headers(key)).status_code
    assert expired_status == 401
    replacement = client.post("/v1/keys/account/rotate", headers=headers).json()["key"]
    revoke_status = client.delete("/v1/keys/account", headers=key_headers(replacement)).status_code
    after_revoke = client.get("/v1/users/me", headers=key_headers(replacement)).status_code
    assert revoke_status == 204
    assert after_revoke == 401
