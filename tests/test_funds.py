"""L2: Funds and allocations API."""
import uuid
from tests.conftest import unique_name
from tests.test_runs import BASE_WORKFLOW


def test_create_fund(client):
    """POST /v1/funds creates a fund linked to a pool."""
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("fund_pool"), "risk_profile": "low"},
    )
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("fund_agent"), "public_key": "f" * 32, "roles": ["seller"]},
    )
    r = client.post(
        "/v1/funds",
        json={
            "name": unique_name("fund"),
            "owner_agent_id": agent.json()["id"],
            "pool_id": pool.json()["id"],
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"]
    assert data["pool_id"] == pool.json()["id"]
    assert data["owner_agent_id"] == agent.json()["id"]


def test_create_fund_pool_not_found(client):
    """POST /v1/funds with non-existent pool returns 404."""
    r = client.post(
        "/v1/funds",
        json={"name": unique_name("f"), "pool_id": str(uuid.uuid4())},
    )
    assert r.status_code == 404


def test_list_and_get_fund(client):
    """GET /v1/funds and GET /v1/funds/{id}."""
    pool = client.post("/v1/pools", json={"name": unique_name("fp"), "risk_profile": "medium"})
    create = client.post("/v1/funds", json={"name": unique_name("myfund"), "pool_id": pool.json()["id"]})
    fund_id = create.json()["id"]
    r = client.get("/v1/funds", params={"limit": 10})
    assert r.status_code == 200
    assert any(f["id"] == fund_id for f in r.json()["items"])
    r2 = client.get(f"/v1/funds/{fund_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == fund_id


def test_add_allocation_and_performance(client, base_vertical_id):
    """POST /v1/funds/{id}/allocate and GET /v1/funds/{id}/performance."""
    vid = base_vertical_id
    pool = client.post("/v1/pools", json={"name": unique_name("perf_p"), "risk_profile": "low"})
    fund_r = client.post("/v1/funds", json={"name": unique_name("perf_f"), "pool_id": pool.json()["id"]})
    fund_id = fund_r.json()["id"]
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("pa"), "public_key": "p" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("ps"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    version_id = ver.json()["id"]
    alloc_r = client.post(
        f"/v1/funds/{fund_id}/allocate",
        json={"strategy_version_id": version_id, "weight": 0.5},
    )
    assert alloc_r.status_code == 201
    assert alloc_r.json()["fund_id"] == fund_id
    assert float(alloc_r.json()["weight"]) == 0.5
    perf_r = client.get(f"/v1/funds/{fund_id}/performance")
    assert perf_r.status_code == 200
    data = perf_r.json()
    assert data["fund_id"] == fund_id
    assert "allocations" in data
    assert "evaluation_summary" in data
    assert len(data["allocations"]) >= 1


def test_fund_not_found(client, base_vertical_id):
    """GET /v1/funds/{id} and allocate return 404 for non-existent fund."""
    vid = base_vertical_id
    r = client.get(f"/v1/funds/{uuid.uuid4()}")
    assert r.status_code == 404
    client.post("/v1/pools", json={"name": unique_name("np"), "risk_profile": "low"})
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("na"), "public_key": "n" * 32, "roles": ["seller"]},
    )
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("ns"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": {**BASE_WORKFLOW, "vertical_id": vid}},
    )
    r2 = client.post(
        f"/v1/funds/{uuid.uuid4()}/allocate",
        json={"strategy_version_id": ver.json()["id"], "weight": 0.3},
    )
    assert r2.status_code == 404