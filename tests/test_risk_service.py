"""Unit tests for risk policy DSL (ROADMAP 2.4)."""

from app.services.risk import (
    merge_policy,
    _effective_drawdown_limit,
    get_effective_limits,
    get_circuit_breaker_spec,
    get_reputation_gate,
    get_graph_gate,
    get_step_scorers,
    make_risk_callback,
)
from app.engine.interpreter import RunResult


def test_merge_policy():
    a = {"max_steps": 100}
    b = {"max_steps": 200, "max_loss_pct": 0.1}
    assert merge_policy([a, b]) == {"max_steps": 200, "max_loss_pct": 0.1}
    assert merge_policy([None, a]) == {"max_steps": 100}


def test_effective_drawdown_limit():
    assert _effective_drawdown_limit(None) is None
    assert _effective_drawdown_limit({}) is None
    assert _effective_drawdown_limit({"max_loss_pct": 0.05}) == 0.05
    assert _effective_drawdown_limit({"max_drawdown": 0.2}) == 0.2
    assert _effective_drawdown_limit({"max_drawdown": 0.2, "max_loss_pct": 0.1}) == 0.2


def test_get_effective_limits_dsl():
    limits = get_effective_limits(None, None)
    assert limits["max_steps"] == 1000
    assert limits["max_runtime_ms"] == 60_000
    assert "max_drawdown" in limits
    assert "max_position_size_pct" in limits
    assert "max_external_calls" in limits
    assert limits["max_external_calls"] is None

    policy = {
        "max_drawdown": 0.15,
        "max_position_size_pct": 0.1,
        "max_steps": 50,
        "max_external_calls": 10,
        "circuit_breaker": {"metric": "daily_loss", "threshold": 0.05},
    }
    limits = get_effective_limits(policy, None)
    assert limits["max_steps"] == 50
    assert limits["max_drawdown"] == 0.15
    assert limits["max_position_size_pct"] == 0.1
    assert limits["max_external_calls"] == 10

    limits = get_effective_limits(policy, {"max_steps": 30})
    assert limits["max_steps"] == 30


def test_get_reputation_gate():
    assert get_reputation_gate(None) is None
    assert get_reputation_gate({}) is None
    assert get_reputation_gate({"min_trust_score": 0.5}) == {
        "min_trust_score": 0.5,
        "min_reputation_score": None,
        "reputation_window": "90d",
    }
    assert get_reputation_gate({"min_reputation_score": 20, "reputation_window": "30d"}) == {
        "min_trust_score": None,
        "min_reputation_score": 20.0,
        "reputation_window": "30d",
    }
    assert get_reputation_gate({"min_trust_score": 0.3, "min_reputation_score": 10})["min_trust_score"] == 0.3
    assert get_reputation_gate({"min_trust_score": 2}) is None  # > 1 clamped out
    assert get_reputation_gate({"min_reputation_score": 101}) is None  # > 100


def test_get_graph_gate():
    assert get_graph_gate(None) is None
    assert get_graph_gate({}) is None
    assert get_graph_gate({"max_reciprocity_score": 0.8}) == {"max_reciprocity_score": 0.8}
    assert get_graph_gate({"max_reciprocity_score": 1.0}) == {"max_reciprocity_score": 1.0}
    assert get_graph_gate({"max_reciprocity_score": 1.5}) is None  # > 1
    assert get_graph_gate({"max_reciprocity_score": -0.1}) is None
    assert get_graph_gate({"max_suspicious_density": 0.5}) == {"max_suspicious_density": 0.5}
    assert get_graph_gate({"max_cluster_size": 5}) == {"max_cluster_size": 5}
    assert get_graph_gate({"max_cluster_size": 1}) == {"max_cluster_size": 1}
    assert get_graph_gate({"max_cluster_size": 0}) is None  # must be >= 1
    assert get_graph_gate({"block_if_in_cycle": True}) == {"block_if_in_cycle": True}
    assert get_graph_gate({"block_if_in_cycle": False}) is None  # only True is stored
    assert get_graph_gate({
        "max_reciprocity_score": 0.3,
        "max_cluster_size": 10,
        "block_if_in_cycle": True,
    }) == {"max_reciprocity_score": 0.3, "max_cluster_size": 10, "block_if_in_cycle": True}


def test_get_step_scorers():
    assert get_step_scorers(None) == []
    assert get_step_scorers({}) == []
    assert get_step_scorers({"record_quality_score": True}) == ["quality"]
    assert get_step_scorers({"record_quality_score": False}) == []
    assert get_step_scorers({"step_scorers": ["quality"]}) == ["quality"]
    assert get_step_scorers({"step_scorers": ["quality", "custom"]}) == ["quality", "custom"]
    assert get_step_scorers({"record_quality_score": True, "step_scorers": ["custom"]}) == ["quality", "custom"]


def test_get_circuit_breaker_spec():
    assert get_circuit_breaker_spec(None) is None
    assert get_circuit_breaker_spec({}) is None
    assert get_circuit_breaker_spec({"circuit_breaker": {}}) is None
    assert get_circuit_breaker_spec({"circuit_breaker": {"metric": "daily_loss", "threshold": 0.05}}) == {
        "metric": "daily_loss",
        "threshold": 0.05,
    }


def test_make_risk_callback_uses_max_drawdown():
    policy = {"max_drawdown": 0.5}
    callback = make_risk_callback(policy)
    result = RunResult(state="succeeded", context={})
    context = {"_start_equity": 100.0, "_equity_curve": [100, 80, 40]}
    callback(result, context)
    assert result.state == "killed"
    assert result.failure_reason == "max_loss_pct"
