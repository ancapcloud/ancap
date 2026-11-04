"""Runs: request run, list, get, logs."""
import uuid
from tests.conftest import unique_name

# BaseVertical (seed) actions: const, math_*, cmp, if, rand_uniform, portfolio_buy, portfolio_sell
BASE_WORKFLOW = {
    "vertical_id": "",  # set from BaseVertical id
    "version": "1.0",
    "steps": [
        {"id": "s1", "action": "const", "args": {"value": 1}, "save_as": "x"},
        {"id": "s2", "action": "math_add", "args": {"a": {"ref": "x"}, "b": 2}},
    ],
}


def _get_base_vertical_id(client):
    r = client.get("/v1/verticals", params={"limit": 200})
    for v in r.json().get("items") or []:
        if v.get("name") == "BaseVertical":
            return v["id"]
    raise RuntimeError("BaseVertical not found (run migration 002)")


def test_request_run(client, base_vertical_id):
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("run_agent"), "public_key": "r" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("run_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    sid = strat.json()["id"]
    ver = client.post(
        f"/v1/strategies/{sid}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    version_id = ver.json()["id"]
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("run_pool"), "risk_profile": "experimental"},
    )
    pool_id = pool.json()["id"]
    r = client.post(
        "/v1/runs",
        json={"strategy_version_id": version_id, "pool_id": pool_id},
        headers={"Idempotency-Key": unique_name("idk_run1")},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["state"] == "succeeded"
    # L1 Run Ledger: hashes and lineage
    assert "inputs_hash" in data and data["inputs_hash"]
    assert "workflow_hash" in data and data["workflow_hash"]
    assert "outputs_hash" in data and data["outputs_hash"]
    assert "parent_run_id" in data  # nullable


def test_list_runs_and_logs(client, base_vertical_id):
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("r2"), "public_key": "r" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("r2s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("r2p"), "risk_profile": "low"})
    client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run2")},
    )
    r = client.get("/v1/runs", params={"limit": 5})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    run_id = items[0]["id"]
    r2 = client.get(f"/v1/runs/{run_id}/logs")
    assert r2.status_code == 200
    assert "items" in r2.json()


def test_get_run_by_id(client, base_vertical_id):
    """GET /v1/runs/{id} returns run with hashes and parent_run_id."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("gr"), "public_key": "g" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("gr_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("gr_p"), "risk_profile": "low"})
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run3")},
    )
    run_id = create.json()["id"]
    r = client.get(f"/v1/runs/{run_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == run_id
    assert data["state"] == "succeeded"
    assert "inputs_hash" in data and "workflow_hash" in data and "outputs_hash" in data
    assert "parent_run_id" in data
    assert "env_hash" in data


def test_get_run_artifacts(client, base_vertical_id):
    """GET /v1/runs/{id}/artifacts returns content-addressed hashes (L1 audit)."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("art"), "public_key": "a" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("art_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("art_p"), "risk_profile": "low"})
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run4")},
    )
    run_id = create.json()["id"]
    r = client.get(f"/v1/runs/{run_id}/artifacts")
    assert r.status_code == 200
    data = r.json()
    assert data["run_id"] == run_id
    assert "inputs_hash" in data and "workflow_hash" in data and "outputs_hash" in data
    assert data["inputs_hash"] and data["workflow_hash"] and data["outputs_hash"]
    assert "proof" in data
    assert "env_hash" in data and data["env_hash"]
    r404 = client.get(f"/v1/runs/00000000-0000-0000-0000-000000000000/artifacts")
    assert r404.status_code == 404


def test_request_run_with_parent_run_id(client, base_vertical_id):
    """Lineage: second run can reference first via parent_run_id."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("pr"), "public_key": "p" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("pr_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("pr_p"), "risk_profile": "low"})
    run1 = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run5")},
    )
    run1_id = run1.json()["id"]
    run2 = client.post(
        "/v1/runs",
        json={
            "strategy_version_id": ver.json()["id"],
            "pool_id": pool.json()["id"],
            "parent_run_id": run1_id,
        },
        headers={"Idempotency-Key": unique_name("idk_run6")},
    )
    assert run2.status_code == 201
    assert run2.json()["parent_run_id"] == run1_id


def test_run_allowed_with_graph_gate_max_cluster_size_and_block_if_in_cycle(client, base_vertical_id):
    """With policy max_cluster_size and block_if_in_cycle, run is allowed when owner cluster_size <= cap and not in cycle."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("gateg"), "public_key": "g" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("gateg_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("gateg_p"), "risk_profile": "low"})
    client.post(
        "/v1/risk/limits",
        json={
            "scope_type": "pool",
            "scope_id": pool.json()["id"],
            "policy_json": {"max_cluster_size": 10, "block_if_in_cycle": True},
        },
    )
    r = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run7")},
    )
    assert r.status_code == 201
    assert r.json()["state"] == "succeeded"


def test_run_404_strategy_version_not_found(client):
    """POST /v1/runs with non-existent strategy_version_id returns 404."""
    pool = client.post("/v1/pools", json={"name": unique_name("nf_p"), "risk_profile": "low"})
    r = client.post(
        "/v1/runs",
        json={"strategy_version_id": str(uuid.uuid4()), "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run_nf")},
    )
    assert r.status_code == 404
    assert "not found" in (r.json().get("detail") or "").lower()


def test_get_run_not_found(client):
    """GET /v1/runs/{id} with non-existent id returns 404."""
    r = client.get(f"/v1/runs/{uuid.uuid4()}")
    assert r.status_code == 404
    assert "not found" in (r.json().get("detail") or "").lower()


def test_get_run_steps(client, base_vertical_id):
    """GET /v1/runs/{id}/steps returns Execution DAG (ROADMAP §5): steps with parent_step_index."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("steps"), "public_key": "s" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("steps_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("steps_p"), "risk_profile": "low"})
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run8")},
    )
    run_id = create.json()["id"]
    r = client.get(f"/v1/runs/{run_id}/steps")
    assert r.status_code == 200
    data = r.json()
    assert data["run_id"] == run_id
    assert "steps" in data
    steps = data["steps"]
    assert len(steps) >= 1
    for i, s in enumerate(steps):
        assert s["step_index"] == i
        assert "step_id" in s and "action" in s and "state" in s
        assert s["parent_step_index"] == (i - 1 if i > 0 else None)
        assert s["state"] in ("succeeded", "failed", "skipped")
    # artifact_hash filled for step-level content addressing (§5)
    if steps:
        assert "artifact_hash" in steps[0]
        assert steps[0]["artifact_hash"] is None or isinstance(steps[0]["artifact_hash"], str)
        assert "score_value" in steps[0] and "score_type" in steps[0]
        assert steps[0]["score_type"] == "outcome"
        assert steps[0]["score_value"] in (0.0, 0.5, 1.0)
        assert "scores" in steps[0]
        score_types = [x["score_type"] for x in steps[0]["scores"]]
        assert "outcome" in score_types
        assert "latency" in score_types


def test_run_steps_quality_score_when_policy_has_record_quality_score(as_platform_admin, client, base_vertical_id):
    """When policy has record_quality_score: true, GET /v1/runs/{id}/steps returns quality in scores (ROADMAP §5)."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("qual"), "public_key": "q" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("qual_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("qual_p"), "risk_profile": "low"})
    client.post(
        "/v1/risk/limits",
        json={
            "scope_type": "pool",
            "scope_id": pool.json()["id"],
            "policy_json": {"record_quality_score": True},
        },
    )
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run9")},
    )
    assert create.status_code == 201
    run_id = create.json()["id"]
    r = client.get(f"/v1/runs/{run_id}/steps")
    assert r.status_code == 200
    steps = r.json().get("steps") or []
    assert len(steps) >= 1
    score_types = [s["score_type"] for s in steps[0]["scores"]]
    assert "quality" in score_types
    quality_entry = next(s for s in steps[0]["scores"] if s["score_type"] == "quality")
    assert 0 <= quality_entry["score_value"] <= 1
    assert isinstance(quality_entry["score_value"], (int, float))


def test_get_run_step_by_index(client, base_vertical_id):
    """GET /v1/runs/{id}/steps/{step_index} returns single step (ROADMAP §5 explainability)."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("stepix"), "public_key": "x" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("stepix_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("stepix_p"), "risk_profile": "low"})
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run10")},
    )
    run_id = create.json()["id"]
    r = client.get(f"/v1/runs/{run_id}/steps/0")
    assert r.status_code == 200
    data = r.json()
    assert data["run_id"] == run_id and data["step_index"] == 0
    assert "step_id" in data and "action" in data and "state" in data
    assert "artifact_hash" in data
    r404 = client.get(f"/v1/runs/{run_id}/steps/999")
    assert r404.status_code == 404


def test_replay_run(client, base_vertical_id):
    """POST /v1/runs/replay creates a new run with same inputs as parent (ROADMAP §5 partial replay)."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("replay"), "public_key": "r" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("replay_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("replay_p"), "risk_profile": "low"})
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"], "params": {"x": 1}},
        headers={"Idempotency-Key": unique_name("idk_replay_parent")},
    )
    assert create.status_code == 201
    run_id = create.json()["id"]
    replay = client.post("/v1/runs/replay", json={"run_id": run_id})
    assert replay.status_code == 201
    data = replay.json()
    assert data["parent_run_id"] == run_id
    assert data["strategy_version_id"] == ver.json()["id"] and data["pool_id"] == pool.json()["id"]
    assert data["id"] != run_id


def test_replay_run_not_found(client):
    r = client.post("/v1/runs/replay", json={"run_id": str(uuid.uuid4())})
    assert r.status_code == 404


def test_replay_from_step_index_success(client, base_vertical_id):
    """POST /v1/runs/replay with from_step_index=1 creates run that executes from step 1 (ROADMAP §5)."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("replay_n"), "public_key": "r" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("replay_n_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("replay_n_p"), "risk_profile": "low"})
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_run11")},
    )
    assert create.status_code == 201
    run_id = create.json()["id"]
    steps_list = client.get(f"/v1/runs/{run_id}/steps")
    assert steps_list.status_code == 200
    assert len(steps_list.json()["steps"]) == 2  # s1, s2
    replay = client.post("/v1/runs/replay", json={"run_id": run_id, "from_step_index": 1})
    assert replay.status_code == 201
    data = replay.json()
    assert data["parent_run_id"] == run_id
    assert data["id"] != run_id
    replay_steps = client.get(f"/v1/runs/{data['id']}/steps")
    assert replay_steps.status_code == 200
    # Replay from step 1: only workflow step index 1 executed -> 1 step in new run
    assert len(replay_steps.json()["steps"]) == 1


def test_replay_from_step_index_no_stored_context(client, base_vertical_id):
    """POST /v1/runs/replay with from_step_index when no step (N-1) or no context_after returns 400."""
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("replay_400"), "public_key": "r" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("replay_400_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("replay_400_p"), "risk_profile": "low"})
    create = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_replay_400_parent")},
    )
    run_id = create.json()["id"]
    # from_step_index=10 but run has only 2 steps -> no step with step_index=9
    r = client.post("/v1/runs/replay", json={"run_id": run_id, "from_step_index": 10})
    assert r.status_code == 400
    assert "No stored context" in (r.json().get("detail") or "")


def test_list_runs_pagination(client):
    """GET /v1/runs returns items and next_cursor structure."""
    r = client.get("/v1/runs", params={"limit": 5})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "next_cursor" in data
