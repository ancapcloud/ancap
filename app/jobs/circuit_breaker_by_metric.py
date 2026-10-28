"""Circuit breaker by metric (ROADMAP 2.4): evaluate policy circuit_breaker and set halted."""
from app.services.recoverable_errors import report_optional_failure
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RiskPolicy, CircuitBreaker, Run, RunStateEnum
from app.db.models import MetricRecord
from app.services.risk import get_circuit_breaker_spec


async def _daily_loss_for_pool(session: AsyncSession, pool_id: UUID) -> float | None:
    """Average return_pct (as fraction 0..1) for runs in pool that ended in last 24h. None if no runs."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    q = select(Run.id).where(
        Run.pool_id == pool_id,
        Run.ended_at >= since,
        Run.state.in_([RunStateEnum.succeeded, RunStateEnum.failed, RunStateEnum.killed]),
    )
    r = await session.execute(q)
    run_ids = [row[0] for row in r.all()]
    if not run_ids:
        return None
    mq = select(MetricRecord.run_id, MetricRecord.name, MetricRecord.value).where(
        MetricRecord.run_id.in_(run_ids),
        MetricRecord.name == "return_pct",
    )
    mr = await session.execute(mq)
    returns = []
    for run_id, name, value in mr.all():
        try:
            if isinstance(value, (int, float)):
                returns.append(float(value))
            elif isinstance(value, dict) and "return_pct" in value:
                returns.append(float(value["return_pct"]))
            else:
                returns.append(float(value))
        except (TypeError, ValueError):
            report_optional_failure('app.jobs.circuit_breaker_by_metric:_daily_loss_for_pool:isinstance', quiet=False)
    if not returns:
        return None
    return sum(returns) / len(returns)  # avg return_pct


async def circuit_breaker_by_metric_tick(
    session: AsyncSession,
    commit: bool = False,
) -> dict:
    """
    For each risk policy with circuit_breaker spec (e.g. metric=daily_loss, threshold=0.05),
    compute the metric for the scope; if >= threshold, set CircuitBreaker state to halted.
    Returns { "evaluated": int, "tripped": int }.
    """
    q = select(RiskPolicy).where(RiskPolicy.policy_json.isnot(None))
    r = await session.execute(q)
    policies = r.scalars().all()
    evaluated = 0
    tripped = 0
    for pol in policies:
        spec = get_circuit_breaker_spec(pol.policy_json or {})
        if not spec:
            continue
        metric_name = spec.get("metric")
        threshold = spec.get("threshold")
        if metric_name is None or threshold is None:
            continue
        scope_type = pol.scope_type
        scope_id = pol.scope_id
        if scope_type != "pool":
            continue
        evaluated += 1
        value: float | None = None
        if metric_name == "daily_loss":
            value_raw = await _daily_loss_for_pool(session, UUID(scope_id) if isinstance(scope_id, str) else scope_id)
            if value_raw is not None:
                value = max(0.0, -value_raw / 100.0)  # loss as positive fraction
        if value is not None and value >= float(threshold):
            cb_q = select(CircuitBreaker).where(
                CircuitBreaker.scope_type == scope_type,
                CircuitBreaker.scope_id == scope_id,
            ).limit(1)
            cb_r = await session.execute(cb_q)
            cb = cb_r.scalar_one_or_none()
            if cb:
                cb.state = "halted"
            else:
                session.add(CircuitBreaker(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    state="halted",
                ))
            tripped += 1
    if commit:
        await session.commit()
    return {"evaluated": evaluated, "tripped": tripped}
