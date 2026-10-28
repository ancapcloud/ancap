"""Evaluation score v0: aggregate metrics per strategy_version, score formula, percentile in vertical."""
from app.services.recoverable_errors import report_optional_failure
import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Run, RunStateEnum, Evaluation, StrategyVersion, Strategy, MetricRecord


def compute_score(sample_size: int, avg_return_pct: float, avg_drawdown_pct: float, killed_rate: float) -> tuple[float, float]:
    """score 0..1, confidence 0..1."""
    r = max(-1, min(1, avg_return_pct / 100.0))
    d = max(0, min(1, avg_drawdown_pct / 100.0))
    k = max(0, min(1, killed_rate))
    r_norm = (r + 1) / 2
    score_raw = 0.55 * r_norm + 0.35 * (1 - d) + 0.10 * (1 - k)
    score = max(0, min(1, score_raw))
    confidence = max(0, min(1, math.log(1 + sample_size) / math.log(1 + 50)))
    return score, confidence


async def update_evaluation_for_version(session: AsyncSession, strategy_version_id: UUID) -> None:
    """Aggregate succeeded runs for this strategy_version; compute score and percentile; upsert Evaluation."""
    run_ids_q = select(Run.id).where(
        Run.strategy_version_id == strategy_version_id,
        Run.state == RunStateEnum.succeeded,
    )
    r = await session.execute(run_ids_q)
    run_ids = [row[0] for row in r.all()]
    if not run_ids:
        return

    metrics_q = select(MetricRecord.run_id, MetricRecord.name, MetricRecord.value).where(MetricRecord.run_id.in_(run_ids))
    res = await session.execute(metrics_q)
    by_run: dict = {}
    for run_id, name, value in res.all():
        if run_id not in by_run:
            by_run[run_id] = {}
        by_run[run_id][name] = value

    sample_size = len(run_ids)
    returns, drawdowns, killed_count = [], [], 0
    for run_id in run_ids:
        m = by_run.get(run_id) or {}
        if "return_pct" in m:
            try:
                returns.append(float(m["return_pct"]))
            except (TypeError, ValueError):
                report_optional_failure('app.services.evaluation:update_evaluation_for_version:returns.append', quiet=True)
        if "max_drawdown_pct" in m:
            try:
                drawdowns.append(float(m["max_drawdown_pct"]))
            except (TypeError, ValueError):
                report_optional_failure('app.services.evaluation:update_evaluation_for_version:drawdowns.append', quiet=True)
        if m.get("risk_breaches", 0):
            killed_count += 1

    avg_return_pct = sum(returns) / len(returns) if returns else 0
    avg_drawdown_pct = sum(drawdowns) / len(drawdowns) if drawdowns else 0
    killed_rate = killed_count / sample_size if sample_size else 0
    score, confidence = compute_score(sample_size, avg_return_pct, avg_drawdown_pct, killed_rate)

    # Same vertical: strategies with same vertical_id
    ver = await session.get(StrategyVersion, strategy_version_id)
    if not ver:
        return
    strat = await session.get(Strategy, ver.strategy_id)
    if not strat:
        return
    vert_id = strat.vertical_id
    strat_ids_q = select(Strategy.id).where(Strategy.vertical_id == vert_id)
    strats = await session.execute(strat_ids_q)
    strategy_ids = [s[0] for s in strats.all()]
    version_ids_q = select(StrategyVersion.id).where(StrategyVersion.strategy_id.in_(strategy_ids))
    vres = await session.execute(version_ids_q)
    version_ids = [v[0] for v in vres.all()]

    evals_q = select(Evaluation).where(Evaluation.strategy_version_id.in_(version_ids))
    evals_res = await session.execute(evals_q)
    evals_list = list(evals_res.scalars().all())
    scores_by_version = {str(e.strategy_version_id): float(e.score) for e in evals_list}
    scores_by_version[str(strategy_version_id)] = score
    sorted_versions = sorted(scores_by_version.keys(), key=lambda vid: scores_by_version[vid], reverse=True)
    rank = sorted_versions.index(str(strategy_version_id))
    percentile = rank / (len(sorted_versions) - 1) if len(sorted_versions) > 1 else 1.0

    ev_q = select(Evaluation).where(Evaluation.strategy_version_id == strategy_version_id)
    er = await session.execute(ev_q)
    ev = er.scalar_one_or_none()
    if ev:
        ev.score = score
        ev.confidence = confidence
        ev.sample_size = sample_size
        ev.percentile_in_vertical = percentile
    else:
        ev = Evaluation(
            strategy_version_id=strategy_version_id,
            score=score,
            confidence=confidence,
            sample_size=sample_size,
            percentile_in_vertical=percentile,
        )
        session.add(ev)
    await session.flush()
