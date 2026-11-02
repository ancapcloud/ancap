"""Embodied AI security control plane."""
from __future__ import annotations

from app.main import app
from app.services import embodied_ai as svc


def test_embodied_ai_route_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/v1/embodied-ai/security" in paths


def test_embodied_ai_security_status_default_off(client, monkeypatch):
    monkeypatch.setenv("FF_EMBODIED_ADAPTER", "false")
    from app.config import get_settings

    get_settings.cache_clear()

    res = client.get("/v1/embodied-ai/security", headers={"Authorization": ""})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["feature_enabled"] is False
    assert body["inference_on_api_host"] is False
    assert body["weights_on_api_host"] is False
    assert body["controls_doc"] == "docs/EMBODIED_AI_SECURITY_CONTROLS.md"
    assert len(body["policy"]) >= 6
    models = body["approved_models"]
    assert any(m["model_id"] == "unitree-unifolm-wla-1.0" for m in models)
    unifolm = next(m for m in models if m["model_id"] == "unitree-unifolm-wla-1.0")
    assert unifolm["adapters_allowed"] is False
    assert unifolm["ancap_status"] == "pending_digest"
    assert unifolm["weight_digest_sha256"] is None


def test_require_adapter_enabled_blocks():
    from fastapi import HTTPException
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        svc.require_adapter_enabled()
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 503
