"""Risk checks v0: policy DSL, max_drawdown/max_loss_pct kill, circuit breaker (ROADMAP 2.4).

Policy JSON schema (declarative; keys optional):
  max_drawdown: float (0..1) — alias for max_loss_pct
  max_loss_pct: float (0..1) — kill run when drawdown >= this
  max_position_size_pct: float (0..1) — max single position as share of portfolio (reserved)
  max_steps: int — run isolation (ROADMAP 2.3)
  max_runtime_ms: int — run isolation
  max_action_calls: int — run isolation
  max_external_calls: int — run isolation (reserved for when interpreter has external calls)
  circuit_breaker: { "metric": str, "threshold": float } — e.g. daily_loss, 0.05 (evaluated by jobs)
  min_trust_score: float (0..1) — block run if strategy owner's trust_score < this (ROADMAP 2.2)
  min_reputation_score: float (0..100) — block run if strategy owner's reputation snapshot score < this
  reputation_window: str — e.g. "90d" for trust/snapshot lookup (default "90d")
  max_reciprocity_score: float (0..1) — block run if strategy owner's graph reciprocity_score >= this (ROADMAP 2.1 anti-sybil)
  max_suspicious_density: float (0..1) — block run if strategy owner's suspicious_density >= this (small dense cluster)
  max_cluster_size: int (>= 1) — block run if strategy owner's cluster_size (order-graph component) > this
  block_if_in_cycle: bool — block run if strategy owner lies on a directed cycle in order graph
  record_quality_score: bool — if true, add step_scorers placeholder "quality" (ROADMAP §5)
  step_scorers: list[str] — e.g. ["quality"]; for each step write RunStepScore with score_value=0.5 (placeholder)
"""
from app.services.recoverable_errors import report_optional_failure

from app.engine.interpreter import RunResult


def merge_policy(layers: list[dict]) -> dict:
    """Merge policy layers (later overrides)."""
    out = {}
    for p in layers:
        if p:
            out.update(p)
    return out


def _effective_drawdown_limit(policy: dict) -> float | None:
    """Single source: max_drawdown or max_loss_pct (DSL: both allowed)."""
    if policy is None:
        return None
    v = policy.get("max_drawdown") if policy.get("max_drawdown") is not None else policy.get("max_loss_pct")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def make_risk_callback(policy: dict):
    """Return a callback for interpreter: kill run if max_drawdown/max_loss_pct breached."""
    max_loss_pct = _effective_drawdown_limit(policy or {})
    if max_loss_pct is None:
        return lambda result, context: None

    def callback(result: RunResult, context: dict) -> None:
        equity_curve = context.get("_equity_curve") or []
        start = context.get("_start_equity") or 10000.0
        if not equity_curve:
            return
        peak = start
        for e in equity_curve:
            if e > peak:
                peak = e
            if peak > 0:
                drawdown = (peak - e) / peak
                if drawdown >= max_loss_pct:
                    result.state = "killed"
                    result.failure_reason = "max_loss_pct"
                    return

    return callback


def get_circuit_breaker_spec(policy: dict) -> dict | None:
    """Return circuit_breaker config from policy if present: { metric, threshold }."""
    if not policy or "circuit_breaker" not in policy:
        return None
    cb = policy.get("circuit_breaker")
    if not isinstance(cb, dict):
        return None
    metric = cb.get("metric")
    threshold = cb.get("threshold")
    if metric is None or threshold is None:
        return None
    try:
        return {"metric": str(metric), "threshold": float(threshold)}
    except (TypeError, ValueError):
        return None


def get_effective_limits(policy: dict, run_limits: dict | None) -> dict:
    """Effective limits for interpreter from policy DSL (ROADMAP 2.4, 2.3 run isolation)."""
    out = {
        "max_steps": 1000,
        "max_runtime_ms": 60_000,
        "max_action_calls": 500,
        "max_external_calls": None,
        "max_drawdown": _effective_drawdown_limit(policy or {}),
        "max_position_size_pct": None,
    }
    if policy:
        for k in ("max_steps", "max_runtime_ms", "max_action_calls", "max_external_calls"):
            if k in policy and policy[k] is not None:
                try:
                    out[k] = int(policy[k])
                except (TypeError, ValueError):
                    report_optional_failure('app.services.risk:get_effective_limits:int', quiet=True)
        if "max_position_size_pct" in policy and policy["max_position_size_pct"] is not None:
            try:
                out["max_position_size_pct"] = float(policy["max_position_size_pct"])
            except (TypeError, ValueError):
                report_optional_failure('app.services.risk:get_effective_limits:float', quiet=True)
    if run_limits:
        for k in ("max_steps", "max_runtime_ms", "max_action_calls", "max_external_calls"):
            if k in run_limits and run_limits[k] is not None:
                out[k] = run_limits[k]
    return out


def get_reputation_gate(policy: dict) -> dict | None:
    """Return reputation gate from policy if present: min_trust_score (0..1), min_reputation_score (0..100), reputation_window."""
    if not policy:
        return None
    min_trust = policy.get("min_trust_score")
    min_rep = policy.get("min_reputation_score")
    if min_trust is None and min_rep is None:
        return None
    out: dict = {
        "min_trust_score": None,
        "min_reputation_score": None,
        "reputation_window": (policy.get("reputation_window") or "90d").strip() or "90d",
    }
    if min_trust is not None:
        try:
            t = float(min_trust)
            if 0 <= t <= 1:
                out["min_trust_score"] = t
        except (TypeError, ValueError):
            report_optional_failure('app.services.risk:get_reputation_gate:float', quiet=True)
    if min_rep is not None:
        try:
            r = float(min_rep)
            if 0 <= r <= 100:
                out["min_reputation_score"] = r
        except (TypeError, ValueError):
            report_optional_failure('app.services.risk:get_reputation_gate:float', quiet=True)
    if out["min_trust_score"] is None and out["min_reputation_score"] is None:
        return None
    return out


def get_graph_gate(policy: dict) -> dict | None:
    """Return graph gate from policy: max_reciprocity_score, max_suspicious_density, max_cluster_size, block_if_in_cycle."""
    if not policy:
        return None
    out = {}
    try:
        if policy.get("max_reciprocity_score") is not None:
            v = float(policy["max_reciprocity_score"])
            if 0 <= v <= 1:
                out["max_reciprocity_score"] = v
    except (TypeError, ValueError):
        report_optional_failure('app.services.risk:get_graph_gate:policy.get', quiet=True)
    try:
        if policy.get("max_suspicious_density") is not None:
            v = float(policy["max_suspicious_density"])
            if 0 <= v <= 1:
                out["max_suspicious_density"] = v
    except (TypeError, ValueError):
        report_optional_failure('app.services.risk:get_graph_gate:policy.get', quiet=True)
    try:
        if policy.get("max_cluster_size") is not None:
            v = int(policy["max_cluster_size"])
            if v >= 1:
                out["max_cluster_size"] = v
    except (TypeError, ValueError):
        report_optional_failure('app.services.risk:get_graph_gate:policy.get', quiet=True)
    if policy.get("block_if_in_cycle") is True:
        out["block_if_in_cycle"] = True
    return out if out else None


def get_step_scorers(policy: dict) -> list[str]:
    """ROADMAP §5: optional step_scorers (e.g. quality) from policy; record_quality_score=true adds 'quality'."""
    if not policy:
        return []
    out: list[str] = []
    if policy.get("record_quality_score") is True:
        out.append("quality")
    sc = policy.get("step_scorers")
    if isinstance(sc, list):
        for s in sc:
            if isinstance(s, str) and s.strip() and s.strip() not in out:
                out.append(s.strip())
    return out
