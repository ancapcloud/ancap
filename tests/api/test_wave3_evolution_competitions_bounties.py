from tests.conftest import unique_email, unique_name


def _register_and_login(client) -> str:
    email = unique_email()
    password = "password123"
    r = client.post("/auth/users", json={"email": email, "password": password, "display_name": "Wave3"})
    assert r.status_code in (201, 400), r.text
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _create_strategy(client, token: str, base_vertical_id: str) -> tuple[str, str]:
    ar = client.post(
        "/agents",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": unique_name("w3_agent"), "public_key": "z" * 32, "roles": ["seller"]},
    )
    assert ar.status_code == 201, ar.text
    aid = ar.json()["id"]
    sr = client.post(
        "/strategies",
        json={"name": unique_name("w3_strategy"), "vertical_id": base_vertical_id, "owner_agent_id": aid},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sr.status_code == 201, sr.text
    return sr.json()["id"], aid


def test_wave3_mutation_and_lineage(client, base_vertical_id):
    token = _register_and_login(client)
    strategy_id, _agent_id = _create_strategy(client, token, base_vertical_id)

    create = client.post(
        "/evolution/mutations",
        headers={"Authorization": f"Bearer {token}"},
        json={"parent_strategy_id": strategy_id, "mutation_type": "change_param", "diff_spec": {"k": "v"}},
    )
    assert create.status_code == 201, create.text

    lineage = client.get(f"/evolution/strategies/{strategy_id}/lineage")
    assert lineage.status_code == 200, lineage.text
    assert len(lineage.json()) >= 1


def test_wave3_tournaments_and_bounties(client, base_vertical_id):
    token = _register_and_login(client)
    strategy_id, agent_id = _create_strategy(client, token, base_vertical_id)

    t = client.post(
        "/competitions/tournaments",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Weekly AI Tournament", "scoring_metric": "evaluation_score"},
    )
    assert t.status_code == 201, t.text
    tid = t.json()["id"]

    e = client.post(
        f"/competitions/tournaments/{tid}/entries",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_id": strategy_id, "agent_id": agent_id},
    )
    assert e.status_code == 201, e.text

    lb = client.get(f"/competitions/tournaments/{tid}/leaderboard")
    assert lb.status_code == 200, lb.text
    assert len(lb.json()) >= 1

    b = client.post(
        "/bounties/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Sybil bypass attempt", "description": "Repro steps", "severity": "high"},
    )
    assert b.status_code == 201, b.text

    lst = client.get("/bounties/reports", headers={"Authorization": f"Bearer {token}"})
    assert lst.status_code == 200, lst.text
    assert len(lst.json()) >= 1
