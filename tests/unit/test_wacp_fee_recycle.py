"""Fee recycle eligibility uses treasury ledger revenue."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.wacp_fee_recycle import fee_recycle_eligibility


def test_operator_cli_preserves_zero_window_and_does_not_invent_oracle_state(monkeypatch, capsys):
    import json
    from scripts.wacp import fee_recycle_check as cli
    monkeypatch.setattr("sys.argv", ["fee_recycle_check.py"])
    monkeypatch.setattr(cli, "_fetch_treasury", lambda _: {"ledger": {"revenue_30d": "0", "revenue_total": "999"}})
    assert cli.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["eligible"] is False
    assert report["ledger_revenue_acp"] == "0"
    assert report["oracle_use_v3"] is None


@pytest.mark.parametrize("threshold", ["0", "-1", "NaN", "Infinity", "bad"])
def test_operator_cli_rejects_invalid_threshold_before_network(monkeypatch, capsys, threshold):
    import json
    from scripts.wacp import fee_recycle_check as cli
    monkeypatch.setattr("sys.argv", ["fee_recycle_check.py", "--min-revenue-acp", threshold])
    def must_not_fetch(_):
        raise AssertionError("Invalid thresholds must be rejected before network access")
    monkeypatch.setattr(cli, "_fetch_treasury", must_not_fetch)
    assert cli.main() == 1
    assert json.loads(capsys.readouterr().out)["eligible"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("revenue", ["0", "NaN", "Infinity", "-1", None, "bad"])
async def test_no_historical_fallback_or_nonfinite_approval(monkeypatch, revenue):
    monkeypatch.setattr("app.services.project_treasury.treasury_status", AsyncMock(
        return_value={"ledger": {"revenue_30d": revenue, "revenue_total": "99999"}}))
    out = await fee_recycle_eligibility(AsyncMock())
    assert out["eligible"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("threshold", ["0", "-1", "NaN", "Infinity", "bad", ""])
async def test_invalid_threshold_fails_closed(monkeypatch, threshold):
    monkeypatch.setattr("app.services.wacp_fee_recycle.get_settings", lambda: SimpleNamespace(
        wacp_fee_recycle_min_revenue_acp=threshold, wacp_v3_pool="", wacp_oracle_use_v3=False))
    monkeypatch.setattr("app.services.project_treasury.treasury_status", AsyncMock(
        return_value={"ledger": {"revenue_30d": "999"}}))
    out = await fee_recycle_eligibility(AsyncMock())
    assert out["eligible"] is False
    assert out["input_valid"] is False


@pytest.mark.asyncio
async def test_fee_recycle_not_eligible_below_threshold(monkeypatch):
    status = SimpleNamespace(
        ledger=SimpleNamespace(revenue_30d="10", revenue_total="10"),
    )
    monkeypatch.setattr(
        "app.services.project_treasury.treasury_status",
        AsyncMock(return_value=status),
    )
    out = await fee_recycle_eligibility(AsyncMock())
    assert out["eligible"] is False
    assert "grow platform spend" in out["reasons"][0]


@pytest.mark.asyncio
async def test_fee_recycle_eligible_above_threshold(monkeypatch):
    status = SimpleNamespace(
        ledger=SimpleNamespace(revenue_30d="120", revenue_total="500"),
    )
    monkeypatch.setattr(
        "app.services.project_treasury.treasury_status",
        AsyncMock(return_value=status),
    )
    out = await fee_recycle_eligibility(AsyncMock())
    assert out["eligible"] is True
    assert out["v3_pool"]
    assert "Do not mint" in out["action"]


@pytest.mark.asyncio
async def test_fee_recycle_boundary_equals_min(monkeypatch):
    status = SimpleNamespace(
        ledger=SimpleNamespace(revenue_30d="50", revenue_total="0"),
    )
    monkeypatch.setattr(
        "app.services.project_treasury.treasury_status",
        AsyncMock(return_value=status),
    )
    out = await fee_recycle_eligibility(AsyncMock())
    assert out["eligible"] is True
    assert out["ledger_revenue_acp"] == "50"
    assert out["min_revenue_acp"] == "50"


@pytest.mark.asyncio
async def test_fee_recycle_missing_ledger_is_zero(monkeypatch):
    monkeypatch.setattr(
        "app.services.project_treasury.treasury_status",
        AsyncMock(return_value=SimpleNamespace()),
    )
    out = await fee_recycle_eligibility(AsyncMock())
    assert out["eligible"] is False
    assert out["ledger_revenue_acp"] == "0"


@pytest.mark.asyncio
async def test_fee_recycle_prefers_revenue_30d_over_total(monkeypatch):
    status = SimpleNamespace(
        ledger=SimpleNamespace(revenue_30d="60", revenue_total="5"),
    )
    monkeypatch.setattr(
        "app.services.project_treasury.treasury_status",
        AsyncMock(return_value=status),
    )
    out = await fee_recycle_eligibility(AsyncMock())
    assert out["eligible"] is True
    assert out["ledger_revenue_acp"] == "60"


@pytest.mark.asyncio
async def test_fee_recycle_never_moves_funds(monkeypatch):
    """Eligibility is a report only — no wrap/LP side effects."""
    status = SimpleNamespace(
        ledger=SimpleNamespace(revenue_30d="999", revenue_total="999"),
    )
    monkeypatch.setattr(
        "app.services.project_treasury.treasury_status",
        AsyncMock(return_value=status),
    )
    out = await fee_recycle_eligibility(AsyncMock())
    assert set(out.keys()) >= {
        "eligible",
        "ledger_revenue_acp",
        "min_revenue_acp",
        "v3_pool",
        "oracle_use_v3",
        "action",
        "reasons",
        "playbook",
    }
    assert "human-signed" in out["action"].lower() or "human" in out["action"].lower()
