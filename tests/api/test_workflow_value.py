import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from decimal import Decimal
from uuid import uuid4

from app.services.workflow_value import workflow_result_hash


def register(client):
    r = client.post("/v1/auth/users", json={"email": f"value_{uuid4().hex}@test.com", "password": "password123", "display_name": "Value fixture"}, headers={"Authorization": ""})
    assert r.status_code in (200, 201), r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def completed_run(client, db_cursor, headers):
    created = client.post("/v1/workflow-store/runs", json={"workflow_slug": "token-risk-report", "payment_currency": "ACP", "unlock_full_result": False, "inputs": {"project_name": "Value fixture"}}, headers=headers)
    assert created.status_code == 201, created.text
    run_id = created.json()["id"]
    db_cursor.execute("UPDATE workflow_runs SET status='completed', result_json=%s::jsonb WHERE id=%s", (json.dumps({"result": "version one"}), run_id))
    db_cursor.connection.commit()
    return run_id, workflow_result_hash({"result": "version one"})


def test_assessment_is_private_immutable_and_not_a_payment(client, db_cursor):
    owner, stranger = register(client), register(client)
    run_id, digest = completed_run(client, db_cursor, owner)
    url = f"/v1/workflow-store/runs/{run_id}/assessment"
    assert client.get(url, headers=stranger).status_code == 404
    body = {"result_hash": digest, "verdict": "accepted", "baseline_minutes": "30", "assisted_minutes": "60", "hourly_rate": "30", "hourly_currency": "USD", "note": "Private review"}
    assert client.post(url, json=body, headers=stranger).status_code == 404
    saved = client.post(url, json=body, headers=owner)
    assert saved.status_code == 201, saved.text
    assert saved.headers["cache-control"] == "private, no-store"
    assert client.post(url, json={**body, "verdict": "rejected"}, headers=owner).status_code == 409
    assert client.patch(url, json=body, headers=owner).status_code == 405
    state = client.get(url, headers=owner)
    assert state.json()["assessment"]["verdict"] == "accepted"
    summary = client.get("/v1/workflow-store/value", headers=owner)
    assert summary.status_code == 200, summary.text
    data = summary.json()
    assert data["completed_count"] == data["assessed_count"] == data["accepted_count"] == 1
    assert Decimal(data["estimated_minutes_saved"]) == -30
    assert data["estimated_labor_value"] == [{"amount": "-15.000000", "currency": "USD"}]
    assert data["ledger_charges"] == []
    assert data["ledger_charges_are_verified_external_payments"] is False
    assert data["scope_basis"] == "completed_runs_created_in_window"
    assert "Private review" not in summary.text
    assert client.get("/v1/workflow-store/value", headers=stranger).json()["completed_count"] == 0
    assert client.get("/v1/workflow-store/value", headers={"Authorization": ""}).status_code == 401


def test_changed_result_excludes_old_assessment_and_requires_re_review(client, db_cursor):
    headers = register(client)
    run_id, digest = completed_run(client, db_cursor, headers)
    url = f"/v1/workflow-store/runs/{run_id}/assessment"
    body = {"result_hash": digest, "verdict": "accepted"}
    assert client.post(url, json=body, headers=headers).status_code == 201
    db_cursor.execute("UPDATE workflow_runs SET result_json=%s::jsonb WHERE id=%s", (json.dumps({"result": "version two"}), run_id))
    db_cursor.connection.commit()
    state = client.get(url, headers=headers).json()
    assert state["assessment"] is None and state["has_stale_assessment"] is True
    summary = client.get("/v1/workflow-store/value", headers=headers).json()
    assert summary["completed_count"] == 1 and summary["assessed_count"] == 0
    assert summary["estimated_minutes_saved"] is None
    assert client.post(url, json=body, headers=headers).status_code == 409
    assert client.post(url, json={**body, "result_hash": state["result_hash"], "verdict": "revision_requested"}, headers=headers).status_code == 201
    db_cursor.execute("SELECT count(*) FROM workflow_result_assessments WHERE workflow_run_id=%s", (run_id,))
    assert db_cursor.fetchone()[0] == 2
    history = client.get(f"/v1/workflow-store/runs/{run_id}/assessments", headers=headers)
    assert history.status_code == 200, history.text
    assert len(history.json()["items"]) == 2
    old = next(item for item in history.json()["items"] if item["result_hash"] == digest)
    archived_url = f"/v1/workflow-store/assessments/{old['id']}/result"
    archived = client.get(archived_url, headers=headers)
    assert archived.status_code == 200 and archived.json()["result"] == {"result": "version one"}
    stranger = register(client)
    assert client.get(archived_url, headers=stranger).status_code == 404
    assert client.get(f"/v1/workflow-store/runs/{run_id}/assessments", headers=stranger).status_code == 404
    db_cursor.execute("UPDATE workflow_result_assessments SET result_snapshot_json='{}'::jsonb WHERE id=%s", (old["id"],))
    db_cursor.connection.commit()
    assert client.get(archived_url, headers=headers).status_code == 409


def test_competing_submissions_cannot_overwrite_the_first_verdict(client, db_cursor):
    headers = register(client)
    run_id, digest = completed_run(client, db_cursor, headers)
    def submit(verdict):
        return client.post(f"/v1/workflow-store/runs/{run_id}/assessment", json={"result_hash": digest, "verdict": verdict}, headers=headers).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, ["accepted", "rejected"]))
    assert sorted(results) == [201, 409]
    db_cursor.execute("SELECT count(*) FROM workflow_result_assessments WHERE workflow_run_id=%s", (run_id,))
    assert db_cursor.fetchone()[0] == 1


def test_invalid_run_and_noncompleted_results_are_not_assessable(client, db_cursor):
    headers = register(client)
    run_id, digest = completed_run(client, db_cursor, headers)
    db_cursor.execute("UPDATE workflow_runs SET status='running' WHERE id=%s", (run_id,))
    db_cursor.connection.commit()
    assert client.get(f"/v1/workflow-store/runs/{run_id}/assessment", headers=headers).status_code == 409
    assert client.post(f"/v1/workflow-store/runs/{run_id}/assessment", json={"result_hash": digest, "verdict": "accepted"}, headers=headers).status_code == 409
    assert client.get("/v1/workflow-store/runs/not-a-uuid/assessment", headers=headers).status_code == 404
    assert client.get("/v1/workflow-store/value?days=91", headers=headers).status_code == 422


def test_summary_is_bounded_to_recent_completed_results(client, db_cursor, monkeypatch):
    from app.services import workflow_value
    monkeypatch.setattr(workflow_value, "VALUE_RUN_LIMIT", 2)
    headers = register(client)
    run_id, digest = completed_run(client, db_cursor, headers)
    db_cursor.execute("UPDATE workflow_runs SET created_at=now()-interval '1 day' WHERE id=%s", (run_id,))
    db_cursor.execute("SELECT owner_user_id FROM workflow_runs WHERE id=%s", (run_id,))
    owner = db_cursor.fetchone()[0]
    db_cursor.executemany("""INSERT INTO workflow_runs (id, owner_user_id, workflow_slug, title, category, status, quoted_amount, quoted_currency, payment_currency, unlock_full_result, result_json, created_at, updated_at)
        VALUES (%s,%s,'fixture','Fixture','test','completed',1,'ACP','ACP',false,'{}'::jsonb,now(),now())""", [(str(uuid4()), str(owner)) for _ in range(3)])
    db_cursor.connection.commit()
    data = client.get("/v1/workflow-store/value", headers=headers).json()
    assert data["truncated"] is True and data["completed_count"] == data["limit"] == 2
    db_cursor.execute("UPDATE workflow_runs SET created_at=now()-interval '91 days' WHERE owner_user_id=%s", (owner,))
    db_cursor.connection.commit()
    data = client.get("/v1/workflow-store/value?days=90", headers=headers).json()
    assert data["completed_count"] == 0 and data["truncated"] is False


def test_value_keeps_acceptance_separate_from_captured_and_refunded_credits(client, monkeypatch):
    from app.config import get_settings
    headers = register(client)
    owner = client.get("/v1/users/me", headers=headers).json()["id"]
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", owner)
    get_settings.cache_clear()
    try:
        deposit = client.post("/v1/ledger/deposit", json={"account_owner_type": "user", "account_owner_id": owner, "amount": {"amount": "1000", "currency": "ACP"}, "reference": "isolated-value-test"}, headers=headers)
        assert deposit.status_code == 201, deposit.text
        created = client.post("/v1/workflow-store/runs", json={"workflow_slug": "token-risk-report", "payment_currency": "ACP", "unlock_full_result": True, "inputs": {"project_name": "Value fixture"}}, headers=headers)
        assert created.status_code == 201, created.text
        run_id = created.json()["id"]
        reserved = client.post(f"/v1/workflow-store/runs/{run_id}/payment-intents", json={"payment_method": "credits"}, headers=headers)
        assert reserved.status_code == 201, reserved.text
        executed = client.post(f"/v1/workflow-store/runs/{run_id}/execute", headers=headers)
        assert executed.status_code == 200, executed.text
        result = executed.json()["item"]
        summary = client.get("/v1/workflow-store/value", headers=headers).json()
        assert summary["assessed_count"] == 0
        assert len(summary["ledger_charges"]) == 1 and summary["ledger_charges"][0]["currency"] == "ACP"
        assert Decimal(summary["ledger_charges"][0]["amount"]) == Decimal(created.json()["price"]["amount"])
        balance_url = f"/v1/ledger/balance?owner_type=user&owner_id={owner}"
        balance_before = client.get(balance_url, headers=headers).json()
        assessed = client.post(f"/v1/workflow-store/runs/{run_id}/assessment", json={"result_hash": result["result_hash"], "verdict": "accepted"}, headers=headers)
        assert assessed.status_code == 201, assessed.text
        assert client.get(balance_url, headers=headers).json() == balance_before
        refund = client.post("/v1/payments/refund-request", json={"payment_intent_id": reserved.json()["item"]["id"], "reason": "Separate test refund action"}, headers=headers)
        assert refund.status_code == 201, refund.text
        approved = client.post(f"/v1/admin/refund-requests/{refund.json()['id']}/approve", json={}, headers=headers)
        assert approved.status_code == 200, approved.text
        summary = client.get("/v1/workflow-store/value", headers=headers).json()
        assert summary["accepted_count"] == 1 and summary["ledger_charges"] == []
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


@pytest.mark.parametrize("purge", ["delete_project", "expire"])
def test_operation_content_lifecycle_removes_all_review_copies(client, db_cursor, monkeypatch, purge):
    from app.config import get_settings
    headers = register(client)
    run_id, digest = completed_run(client, db_cursor, headers)
    owner = client.get("/v1/users/me", headers=headers).json()["id"]
    project = client.post("/v1/workflow-ops/projects", json={"name": "Retention fixture", "context": "Private retained content", "retention_days": 1}, headers=headers)
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]
    automation = client.post("/v1/workflow-ops/automations", json={"name": "Retention fixture", "project_id": project_id, "steps": [{"slug": "token-listing-pack"}], "require_review": True}, headers=headers)
    assert automation.status_code == 201, automation.text
    operation_id = str(uuid4())
    db_cursor.execute("""INSERT INTO workflow_operation_runs (id,owner_user_id,automation_id,request_key,request_hash,kind,state,snapshot_json,progress_json,cost_acp,max_cost_acp,created_at,expires_at)
        VALUES (%s,%s,%s,%s,%s,'manual','completed','{}'::jsonb,%s::jsonb,3,3,now(),now()+interval '1 day')""",
        (operation_id, owner, automation.json()["id"], str(uuid4()), "a"*64, json.dumps({"items": [{"run_id": run_id}]})))
    db_cursor.connection.commit()
    saved = client.post(f"/v1/workflow-store/runs/{run_id}/assessment", json={"result_hash": digest, "verdict": "accepted", "note": "Private retained review"}, headers=headers)
    assert saved.status_code == 201, saved.text
    archived_url = f"/v1/workflow-store/assessments/{saved.json()['id']}/result"
    assert client.get(archived_url, headers=headers).status_code == 200
    try:
        if purge == "delete_project":
            result = client.delete(f"/v1/workflow-ops/projects/{project_id}", headers=headers)
        else:
            db_cursor.execute("UPDATE workflow_operation_runs SET expires_at=now()-interval '1 minute' WHERE id=%s", (operation_id,))
            db_cursor.connection.commit()
            monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", owner)
            get_settings.cache_clear()
            result = client.post("/v1/workflow-ops/tick", headers=headers)
        assert result.status_code == 200, result.text
        assert client.get(archived_url, headers=headers).status_code == 404
        history = client.get(f"/v1/workflow-store/runs/{run_id}/assessments", headers=headers)
        assert history.status_code == 200 and history.json()["items"] == []
        db_cursor.execute("SELECT count(*) FROM workflow_result_assessments WHERE workflow_run_id=%s", (run_id,))
        assert db_cursor.fetchone()[0] == 0
        db_cursor.execute("SELECT state,cost_acp FROM workflow_operation_runs WHERE id=%s", (operation_id,))
        state, amount = db_cursor.fetchone()
        assert state == "expired" and amount == Decimal("3")
        db_cursor.execute("SELECT count(*) FROM workflow_runs WHERE id=%s", (run_id,))
        assert db_cursor.fetchone()[0] == 1
        assert client.get("/v1/workflow-store/value", headers=headers).json()["completed_count"] == 0
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


@pytest.mark.parametrize("literal", ["NULL", "'null'::jsonb"])
def test_database_redaction_removes_archives_even_without_new_worker_helper(client, db_cursor, literal):
    headers = register(client)
    run_id, digest = completed_run(client, db_cursor, headers)
    saved = client.post(f"/v1/workflow-store/runs/{run_id}/assessment", json={"result_hash": digest, "verdict": "accepted", "note": "Private redaction fixture"}, headers=headers)
    assert saved.status_code == 201, saved.text
    # The SQL fragment is a fixed test parameter, never request input.
    db_cursor.execute("UPDATE workflow_runs SET result_json=" + literal + " WHERE id=%s", (run_id,))
    db_cursor.connection.commit()
    db_cursor.execute("SELECT count(*) FROM workflow_result_assessments WHERE workflow_run_id=%s", (run_id,))
    assert db_cursor.fetchone()[0] == 0
    assert client.get(f"/v1/workflow-store/assessments/{saved.json()['id']}/result", headers=headers).status_code == 404
    assert client.get("/v1/workflow-store/value", headers=headers).json()["completed_count"] == 0
