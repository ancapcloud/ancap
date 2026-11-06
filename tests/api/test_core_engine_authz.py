"""Object-level authorization on legacy core-engine routes (2026-11-04 audit).

A stranger (second user that owns neither party agent) must not be able to drive a
contract's money-moving lifecycle, flip the risk kill switch, render dispute verdicts,
publish strategy versions or run the scenario runner.
"""
from tests.conftest import unique_email, unique_name


def _login_new_user(client) -> str:
    email = unique_email()
    password = "password123"
    reg = client.post("/v1/auth/users", json={"email": email, "password": password, "display_name": "Stranger"})
    assert reg.status_code in (201, 400), reg.text
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _agent(client, role: str, headers: dict | None = None) -> str:
    r = client.post(
        "/v1/agents",
        json={"display_name": unique_name(f"authz_{role}"), "public_key": "x" * 32, "roles": [role]},
        headers=headers or {},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _contract(client, employer: str, worker: str) -> str:
    body = {
        "employer_agent_id": employer,
        "worker_agent_id": worker,
        "scope_type": "generic",
        "title": "Authz job",
        "description": "",
        "payment_model": "fixed",
        "fixed_amount_value": "5",
        "currency": "VUSD",
        "max_runs": 1,
    }
    r = client.post("/v1/contracts", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_stranger_cannot_drive_contract_lifecycle(client, base_vertical_id):
    employer = _agent(client, "seller")
    worker = _agent(client, "buyer")
    cid = _contract(client, employer, worker)
    stranger = {"Authorization": f"Bearer {_login_new_user(client)}"}

    for action in ("propose", "accept", "complete", "cancel", "dispute"):
        r = client.post(f"/v1/contracts/{cid}/{action}", headers=stranger)
        assert r.status_code == 403, (action, r.status_code, r.text)

    anon = client.post(f"/v1/contracts/{cid}/complete", headers={"Authorization": ""})
    assert anon.status_code == 401, anon.text


def test_stranger_cannot_create_contract_between_foreign_agents(client, base_vertical_id):
    employer = _agent(client, "seller")
    worker = _agent(client, "buyer")
    stranger = {"Authorization": f"Bearer {_login_new_user(client)}"}
    r = client.post(
        "/v1/contracts",
        json={
            "employer_agent_id": employer,
            "worker_agent_id": worker,
            "scope_type": "generic",
            "title": "Hijack",
            "payment_model": "fixed",
            "fixed_amount_value": "5",
            "currency": "VUSD",
        },
        headers=stranger,
    )
    assert r.status_code == 403, r.text


def test_worker_cannot_release_escrow(client, base_vertical_id):
    """complete() pays the worker from escrow, so only the employer side may call it."""
    worker_token = _login_new_user(client)
    worker_headers = {"Authorization": f"Bearer {worker_token}"}
    employer = _agent(client, "seller")
    worker = _agent(client, "buyer", headers=worker_headers)
    cid = _contract(client, employer, worker)
    client.post(f"/v1/contracts/{cid}/propose")
    accepted = client.post(f"/v1/contracts/{cid}/accept", headers=worker_headers)
    assert accepted.status_code in (200, 400), accepted.text
    r = client.post(f"/v1/contracts/{cid}/complete", headers=worker_headers)
    assert r.status_code in (400, 403), r.text
    assert r.status_code != 200


def test_operator_only_routes_reject_regular_users(client):
    scope = {"scope_type": "pool", "scope_id": "00000000-0000-0000-0000-000000000001"}
    assert client.post("/v1/risk/kill", json=scope).status_code in (403, 503)
    assert client.post("/v1/risk/limits", json={**scope, "policy_json": {}}).status_code in (403, 503)
    assert client.post("/v1/flows/run", json={"flow_id": "flow1"}).status_code in (403, 503)
    verdict = client.post(
        "/v1/disputes/00000000-0000-0000-0000-000000000002/verdict",
        json={"verdict": {"ok": True}, "status": "resolved"},
    )
    assert verdict.status_code in (403, 422, 503), verdict.text
