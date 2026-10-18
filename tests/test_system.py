"""System and health endpoints."""

import os
import time

from sqlalchemy import create_engine, text

from app.api.routers import system as system_router
from app.config import get_settings


def _sync_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    return url


def _get_system_job_run(job_run_id: str):
    engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            return conn.execute(
                text(
                    "SELECT job_name, trigger_source, status, attempts, max_attempts, result_json, last_error, next_retry_at "
                    "FROM system_job_runs WHERE id = :job_run_id"
                ),
                {"job_run_id": job_run_id},
            ).mappings().first()
    finally:
        engine.dispose()


def _wait_for_system_job_run(job_run_id: str, *, statuses: set[str], timeout_s: float = 5.0):
    deadline = time.time() + timeout_s
    last_row = None
    while time.time() < deadline:
        last_row = _get_system_job_run(job_run_id)
        if last_row is not None and last_row["status"] in statuses:
            return last_row
        time.sleep(0.1)
    return last_row


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "ANCAP Core API"
    assert "version" in data


def test_health(client):
    r = client.get("/v1/system/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readiness_shape(client):
    r = client.get("/v1/system/ready")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] in {"ready", "not_ready"}
    assert payload["checks"].keys() >= {"database", "redis"}
    assert isinstance(payload["checks"]["database"], bool)
    assert isinstance(payload["checks"]["redis"], bool)


def test_health_full_public_shape(client):
    r = client.get("/v1/system/health/full")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] in {"ok", "degraded"}
    assert payload["checks"].keys() >= {"database", "redis", "llm", "mail", "bridge", "stripe"}
    assert payload["checks"]["stripe"]["ok"] is True
    assert payload["checks"]["stripe"]["configured"] is False
    assert "acp_rpc" not in payload["checks"]
    assert "acp_rpc_url" not in r.text


def test_jobs_tick(client):
    """POST /v1/system/jobs/tick runs incremental jobs (edges_daily, agent_relationships, auto_*)."""
    r = client.post("/v1/system/jobs/tick")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "edges_daily_orders_processed" in data
    assert isinstance(data["edges_daily_orders_processed"], int)
    assert "agent_relationships_orders_processed" in data
    assert isinstance(data["agent_relationships_orders_processed"], int)
    assert "circuit_breaker_by_metric" in data
    assert data["circuit_breaker_by_metric"].keys() >= {"evaluated", "tripped"}
    assert "reputation_recomputed" in data
    assert isinstance(data["reputation_recomputed"], int)
    assert "ledger_invariant_violations" in data
    assert isinstance(data["ledger_invariant_violations"], list)


def test_jobs_tick_async_returns_accepted(client):
    r = client.post("/v1/system/jobs/tick/async")
    assert r.status_code == 202, r.text
    payload = r.json()
    assert payload["status"] == "queued"
    assert "background" in payload["message"].lower()
    assert payload["job_run_id"]
    assert payload["max_attempts"] == 3


def test_jobs_tick_async_requires_matching_cron_secret_when_configured(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "cron-secret-test")
    get_settings.cache_clear()
    try:
        # Opt out of AuthedTestClient cron injection to assert missing-header behavior.
        missing = client.post("/v1/system/jobs/tick/async", headers={"X-Cron-Secret": ""})
        assert missing.status_code == 403, missing.text
        assert missing.json()["detail"] == "Invalid or missing cron secret"

        wrong = client.post("/v1/system/jobs/tick/async", headers={"X-Cron-Secret": "wrong-secret"})
        assert wrong.status_code == 403, wrong.text
        assert wrong.json()["detail"] == "Invalid or missing cron secret"

        ok = client.post("/v1/system/jobs/tick/async", headers={"X-Cron-Secret": "cron-secret-test"})
        assert ok.status_code == 202, ok.text
        assert ok.json()["status"] == "queued"
    finally:
        monkeypatch.setenv("CRON_SECRET", "test-cron-secret")
        get_settings.cache_clear()


def test_system_jobs_tick_run_records_success(client, monkeypatch):
    async def fake_run_all_jobs(session):
        return {"ok": True, "stub": "success"}

    monkeypatch.setattr(system_router, "_run_all_jobs", fake_run_all_jobs)

    response = client.post("/v1/system/jobs/tick/async")
    assert response.status_code == 202, response.text
    job_run_id = response.json()["job_run_id"]

    row = _wait_for_system_job_run(job_run_id, statuses={"succeeded"})
    assert row is not None
    assert row["job_name"] == "system_jobs_tick"
    assert row["trigger_source"] == "api"
    assert row["status"] == "succeeded"
    assert row["attempts"] == 1
    assert row["max_attempts"] == 3
    assert row["result_json"] == {"ok": True, "stub": "success"}
    assert row["last_error"] is None
    assert row["next_retry_at"] is None


def test_system_jobs_tick_run_records_retry_then_dead_letter(client, monkeypatch):
    async def always_fail(session):
        raise RuntimeError("boom")

    monkeypatch.setattr(system_router, "_run_all_jobs", always_fail)

    response = client.post("/v1/system/jobs/tick/async")
    assert response.status_code == 202, response.text
    job_run_id = response.json()["job_run_id"]

    row = _wait_for_system_job_run(job_run_id, statuses={"retry"})
    assert row is not None
    assert row["status"] == "retry"
    assert row["attempts"] == 1
    assert row["last_error"] == "boom"
    assert row["next_retry_at"] is not None

    engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE system_job_runs SET next_retry_at = created_at WHERE id = :job_run_id"),
                {"job_run_id": job_run_id},
            )
    finally:
        engine.dispose()

    retry_response = client.post("/v1/system/jobs/tick/async")
    assert retry_response.status_code == 202, retry_response.text
    row = _wait_for_system_job_run(job_run_id, statuses={"retry"})
    assert row is not None
    assert row["status"] == "retry"
    assert row["attempts"] == 2
    assert row["next_retry_at"] is not None

    engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE system_job_runs SET next_retry_at = created_at WHERE id = :job_run_id"),
                {"job_run_id": job_run_id},
            )
    finally:
        engine.dispose()

    dead_letter_response = client.post("/v1/system/jobs/tick/async")
    assert dead_letter_response.status_code == 202, dead_letter_response.text
    row = _wait_for_system_job_run(job_run_id, statuses={"dead_letter"})
    assert row is not None
    assert row["status"] == "dead_letter"
    assert row["attempts"] == 3
    assert row["next_retry_at"] is None
    assert row["last_error"] == "boom"


def test_openapi_schema(client):
    """GET /openapi.json returns valid OpenAPI 3 schema with paths."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert data.get("openapi", "").startswith("3.")
    assert "paths" in data
    assert "info" in data
    assert data.get("info", {}).get("title") == "ANCAP Core API"
    operation_ids = [
        operation["operationId"]
        for path in data["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
    ]
    assert len(operation_ids) == len(set(operation_ids)), "OpenAPI operation IDs must be unique"
