from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from app.config import get_settings


def setup_costs(client, monkeypatch):
    registered = client.post("/v1/auth/users", headers={"Authorization": ""}, json={
        "email": f"cost_{uuid4().hex}@test.com", "password": "password123", "display_name": "Cost reviewer"})
    assert registered.status_code in (200, 201), registered.text
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    user = client.get("/v1/users/me", headers=headers).json()["id"]
    monkeypatch.setattr(type(get_settings()), "platform_admin_user_ids_allowlist", property(lambda self: (user,)))
    run = client.post("/v1/workflow-store/runs", headers=headers, json={
        "workflow_slug": "token-risk-report", "payment_currency": "ACP", "unlock_full_result": False,
        "inputs": {"project_name": "Cost fixture"}})
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]
    body = {"source": "provider-test", "document_id": uuid4().hex, "line_id": "1",
        "document_sha256": "a" * 64, "category": "model", "currency": "USD", "amount": "10",
        "review_note": "Disposable test evidence, not a real invoice",
        "allocations": [{"workflow_run_id": run_id, "allocated_amount": "3"}]}
    return headers, run_id, body


def test_private_recording_conflict_and_totals(client, monkeypatch, db_cursor):
    headers, run, body = setup_costs(client, monkeypatch)
    url = "/v1/workflow-store/admin/cost-evidence"
    costs = f"/v1/workflow-store/admin/runs/{run}/costs"
    assert client.post(url, json=body, headers={"Authorization": ""}).status_code == 401
    assert client.get(costs, headers={"Authorization": ""}).status_code == 401
    # The default fixture user is authenticated but not on the reviewer allowlist.
    assert client.post(url, json=body).status_code == 403
    assert client.get(costs).status_code == 403
    before = client.get(costs, headers=headers)
    assert before.json()["totals_by_currency"] == {}
    saved = client.post(url, json=body, headers=headers)
    assert saved.status_code == 201, saved.text
    assert saved.json()["verification_basis"] == "operator_attested"
    assert saved.headers["cache-control"] == "private, no-store"
    assert client.post(url, json={**body, "amount": "20"}, headers=headers).status_code == 409
    result = client.get(costs, headers=headers)
    assert result.headers["cache-control"] == "private, no-store"
    from decimal import Decimal
    assert Decimal(result.json()["totals_by_currency"]["USD"]) == 3
    assert result.json()["coverage_complete"] is False
    assert "review_note" not in result.text and "document_id" not in result.text
    assert client.post(url, json={**body, "document_id": uuid4().hex, "allocations": [
        {"workflow_run_id": str(uuid4()), "allocated_amount": "1"}]}, headers=headers).status_code == 404
    db_cursor.execute("SELECT count(*) FROM workflow_cost_evidence WHERE document_id=%s", (body["document_id"],))
    assert db_cursor.fetchone()[0] == 1


def test_concurrent_source_line_is_recorded_once(client, monkeypatch, db_cursor):
    headers, run, body = setup_costs(client, monkeypatch)
    def submit(_):
        return client.post("/v1/workflow-store/admin/cost-evidence", json=body, headers=headers).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert sorted(results) == [201, 409]
    db_cursor.execute("SELECT count(*) FROM workflow_cost_allocations WHERE workflow_run_id=%s", (run,))
    assert db_cursor.fetchone()[0] == 1


def test_invalid_batch_is_rejected_atomically(client, monkeypatch):
    headers, run, body = setup_costs(client, monkeypatch)
    for allocations in [body["allocations"] * 2, [{"workflow_run_id": run, "allocated_amount": "11"}]]:
        result = client.post("/v1/workflow-store/admin/cost-evidence", json={**body, "allocations": allocations}, headers=headers)
        assert result.status_code == 422, result.text
    assert client.get(f"/v1/workflow-store/admin/runs/{run}/costs", headers=headers).json()["totals_by_currency"] == {}


def test_split_line_retains_source_identity_after_run_deletion(client, monkeypatch, db_cursor):
    headers, first, body = setup_costs(client, monkeypatch)
    created = client.post("/v1/workflow-store/runs", headers=headers, json={
        "workflow_slug": "token-risk-report", "payment_currency": "ACP", "unlock_full_result": False,
        "inputs": {"project_name": "Second cost fixture"}})
    assert created.status_code == 201, created.text
    second = created.json()["id"]
    body["allocations"].append({"workflow_run_id": second, "allocated_amount": "7"})
    url = "/v1/workflow-store/admin/cost-evidence"
    saved = client.post(url, json=body, headers=headers)
    assert saved.status_code == 201, saved.text
    db_cursor.execute("DELETE FROM workflow_runs WHERE id=%s", (first,))
    db_cursor.connection.commit()
    assert client.get(f"/v1/workflow-store/admin/runs/{first}/costs", headers=headers).status_code == 404
    remaining = client.get(f"/v1/workflow-store/admin/runs/{second}/costs", headers=headers)
    from decimal import Decimal
    assert Decimal(remaining.json()["totals_by_currency"]["USD"]) == 7
    assert remaining.json()["costs_are_independently_verified"] is False
    assert client.post(url, json={**body, "allocations": [body["allocations"][1]]}, headers=headers).status_code == 409


def test_get_cost_evidence_by_id(client, monkeypatch):
    """Test GET /admin/cost-evidence/{evidence_id} endpoint."""
    headers, run_id, body = setup_costs(client, monkeypatch)
    
    # First create the evidence
    created = client.post("/v1/workflow-store/admin/cost-evidence", json=body, headers=headers)
    assert created.status_code == 201, created.text
    evidence_id = created.json()["id"]
    
    # Now retrieve it
    retrieved = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}", headers=headers)
    assert retrieved.status_code == 200, retrieved.text
    
    # Verify the response contains all expected fields
    data = retrieved.json()
    assert data["id"] == evidence_id
    assert data["source"] == body["source"]
    assert data["document_id"] == body["document_id"]
    assert data["line_id"] == body["line_id"]
    assert data["document_sha256"] == body["document_sha256"]
    assert data["category"] == body["category"]
    assert data["currency"] == body["currency"]
    assert str(data["amount"]) == str(body["amount"])
    assert data["review_note"] == body["review_note"]
    
    # Verify allocations are included
    assert "allocations" in data
    assert len(data["allocations"]) == 1
    assert data["allocations"][0]["workflow_run_id"] == run_id
    assert str(data["allocations"][0]["allocated_amount"]) == str(body["allocations"][0]["allocated_amount"])
    
    # Verify cache-control header
    assert retrieved.headers["cache-control"] == "private, no-store"
    
    # Test 404 for non-existent evidence
    not_found = client.get(f"/v1/workflow-store/admin/cost-evidence/{uuid4().hex}", headers=headers)
    assert not_found.status_code == 404
    assert "not found" in not_found.text.lower()
    
    # Test unauthorized access
    unauthorized = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}")
    assert unauthorized.status_code == 401
