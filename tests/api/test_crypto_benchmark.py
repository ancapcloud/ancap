"""Crypto benchmark scorecard (QOBLIB-style)."""
from __future__ import annotations

from app.main import app


def test_crypto_benchmark_route_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/v1/crypto/benchmark" in paths


def test_crypto_benchmark_default_composition(client):
    res = client.get("/v1/crypto/benchmark", headers={"Authorization": ""})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["overall"] in ("pass", "fail", "pending")
    assert body["controls_doc"] == "docs/CRYPTO_BENCHMARK_LIBRARY.md"
    assert "qoblib_reference" in body
    assert len(body["classes"]) == 6
    ids = {c["id"] for c in body["classes"]}
    assert ids == {
        "reserve_backing",
        "snapshot_freshness",
        "intent_pipeline",
        "dry_run_honesty",
        "sacp_readiness",
        "contract_trust",
    }
    for cls in body["classes"]:
        assert cls["result"] in ("pass", "fail", "pending")
        assert cls["baseline"]
        assert isinstance(cls["notes"], list)


def test_crypto_benchmark_dry_run_honesty_fail(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_RAIL_ENABLED", "true")
    monkeypatch.setenv("BRIDGE_RAIL_PAUSED", "false")
    monkeypatch.setenv("BRIDGE_DRY_RUN", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    res = client.get("/v1/crypto/benchmark", headers={"Authorization": ""})
    assert res.status_code == 200, res.text
    dry_run = next(c for c in res.json()["classes"] if c["id"] == "dry_run_honesty")
    assert dry_run["result"] == "fail"


def test_crypto_benchmark_sacp_empty_contract_honesty(client, monkeypatch):
    monkeypatch.setenv("FF_SACP", "true")
    monkeypatch.setenv("SACP_CONTRACT", "")
    monkeypatch.setenv("SACP_PAUSED", "false")
    from app.config import get_settings

    get_settings.cache_clear()

    res = client.get("/v1/crypto/benchmark", headers={"Authorization": ""})
    assert res.status_code == 200, res.text
    sacp = next(c for c in res.json()["classes"] if c["id"] == "sacp_readiness")
    assert sacp["result"] == "fail"
    assert any("SACP_CONTRACT" in n for n in sacp["notes"])
