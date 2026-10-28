"""Step-level quality scorer (ROADMAP §5). Built-in heuristic; optional HTTP callback when quality_scorer_url is set."""

from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

import httpx


def compute_step_quality(
    step_id: str,
    action: str,
    state: str,
    duration_ms: int | None,
    result_summary: dict | None,
) -> float:
    """
    Compute quality score 0..1 for a step. Heuristic: blend outcome (success/fail/skip) with latency.
    - outcome_component: 1.0 succeeded, 0.5 skipped, 0.0 failed
    - latency_component: max(0, 1 - duration_ms/10000), rewards fast steps
    - quality = 0.6 * outcome + 0.4 * latency (so success + speed = higher quality)
    """
    outcome = 1.0 if state == "succeeded" else 0.5 if state == "skipped" else 0.0
    latency = max(0.0, 1.0 - ((duration_ms or 0) / 10000.0))
    return round(0.6 * outcome + 0.4 * latency, 4)


async def get_step_quality(
    step_id: str,
    action: str,
    state: str,
    duration_ms: int | None,
    result_summary: dict | None,
    scorer_url: str,
    timeout_seconds: int = 5,
) -> float:
    """
    Return quality score 0..1. If scorer_url is non-empty, POST payload to URL and use JSON {"score": float};
    on timeout, non-2xx, or invalid response fall back to compute_step_quality.
    """
    if not (scorer_url and scorer_url.strip()):
        return compute_step_quality(step_id, action, state, duration_ms, result_summary)
    payload = {
        "step_id": step_id,
        "action": action,
        "state": state,
        "duration_ms": duration_ms,
        "result_summary": result_summary,
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                scorer_url.strip(),
                json=payload,
                timeout=timeout_seconds,
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "score" in data:
                    s = float(data["score"])
                    if 0 <= s <= 1:
                        return round(s, 4)
    except Exception:
        report_optional_failure('app.services.step_quality:get_step_quality:httpx.AsyncClient', quiet=False)
    return compute_step_quality(step_id, action, state, duration_ms, result_summary)
