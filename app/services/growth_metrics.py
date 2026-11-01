from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GrowthMetricRollup, User, Agent, Run, RunStateEnum


def _dims_hash(dimensions: dict) -> str:
    raw = json.dumps(dimensions or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()


async def upsert_metric(
    session: AsyncSession,
    *,
    metric_date: date,
    metric_key: str,
    metric_value: float,
    dimensions: dict | None = None,
) -> None:
    dims = dimensions or {}
    stmt = (
        insert(GrowthMetricRollup)
        .values(
            metric_date=metric_date,
            metric_key=metric_key,
            metric_value=metric_value,
            dimensions_json=dims,
            dimensions_hash=_dims_hash(dims),
        )
        .on_conflict_do_update(
            index_elements=["metric_date", "metric_key", "dimensions_hash"],
            set_={
                "metric_value": metric_value,
                "dimensions_json": dims,
                "created_at": func.now(),
            },
        )
    )
    await session.execute(stmt)


async def rollup_daily_metrics(session: AsyncSession, *, for_date: date | None = None) -> dict:
    d = for_date or datetime.now(timezone.utc).date()
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    user_cnt = (await session.execute(select(func.count()).select_from(User).where(and_(User.created_at >= start, User.created_at < end)))).scalar_one()
    agent_cnt = (await session.execute(select(func.count()).select_from(Agent).where(and_(Agent.created_at >= start, Agent.created_at < end)))).scalar_one()
    run_cnt = (
        await session.execute(
            select(func.count())
            .select_from(Run)
            .where(and_(Run.created_at >= start, Run.created_at < end, Run.state == RunStateEnum.succeeded))
        )
    ).scalar_one()

    await upsert_metric(session, metric_date=d, metric_key="acquisition_users", metric_value=float(user_cnt), dimensions={})
    await upsert_metric(session, metric_date=d, metric_key="acquisition_agents", metric_value=float(agent_cnt), dimensions={})
    await upsert_metric(session, metric_date=d, metric_key="activation_runs_succeeded", metric_value=float(run_cnt), dimensions={})

    return {"date": str(d), "users": int(user_cnt), "agents": int(agent_cnt), "runs_succeeded": int(run_cnt)}

