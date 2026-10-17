"""Oracle must stay on V2 while WACP_ORACLE_USE_V3 is false."""

from __future__ import annotations

from app.config import get_settings
from app.services import market_economy as me


def test_oracle_defaults_to_v2_even_when_v3_pool_configured(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "wacp_v3_pool", me.OFFICIAL_WACP_POOL_V3)
    monkeypatch.setattr(settings, "wacp_oracle_use_v3", False)
    assert me._official_pool_for_oracle() == me.OFFICIAL_WACP_POOL_V2


def test_oracle_uses_v3_when_explicitly_enabled(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "wacp_v3_pool", me.OFFICIAL_WACP_POOL_V3)
    monkeypatch.setattr(settings, "wacp_oracle_use_v3", True)
    assert me._official_pool_for_oracle() == me.OFFICIAL_WACP_POOL_V3


def test_oracle_meta_exposes_bootstrap_and_gate(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "wacp_oracle_use_v3", False)
    meta = me.oracle_meta()
    assert meta["pool"] == me.OFFICIAL_WACP_POOL_V2
    assert meta["pool_v3_bootstrap"] == me.OFFICIAL_WACP_POOL_V3
    assert meta["oracle_use_v3"] is False
