from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Pool,
    PoolStatusEnum,
    RiskProfileEnum,
    Strategy,
    StrategyStatusEnum,
    StrategyVersion,
    Vertical,
    VerticalStatusEnum,
)


@dataclass(frozen=True)
class QuickstartProvision:
    strategy_id: UUID
    strategy_version_id: UUID
    pool_id: UUID


SAFE_WORKFLOW = {
    # Must conform to WorkflowSpec used by interpreter.
    # vertical_id is filled in provision_quickstart().
    "vertical_id": "",
    "version": "1.0",
    "steps": [
        {"id": "hello", "action": "const", "args": {"value": "hello_quickstart"}, "save_as": "hello"},
    ]
}


async def _ensure_vertical(session: AsyncSession) -> Vertical:
    r = await session.execute(
        select(Vertical)
        .where(
            Vertical.name == "BaseVertical",
            Vertical.status == VerticalStatusEnum.active,
        )
        .order_by(Vertical.created_at.asc())
        .limit(1)
    )
    v = r.scalar_one_or_none()
    if v:
        return v
    v = Vertical(name="BaseVertical", status=VerticalStatusEnum.active)
    session.add(v)
    await session.flush()
    return v


async def _ensure_pool(session: AsyncSession) -> Pool:
    r = await session.execute(select(Pool).where(Pool.status == PoolStatusEnum.active).order_by(Pool.created_at.asc()).limit(1))
    p = r.scalar_one_or_none()
    if p:
        return p
    p = Pool(name="Quickstart Pool", risk_profile=RiskProfileEnum.low, status=PoolStatusEnum.active, rules={}, fee_model={})
    session.add(p)
    await session.flush()
    return p


async def provision_quickstart(
    session: AsyncSession,
    *,
    owner_agent_id: UUID,
) -> QuickstartProvision:
    v = await _ensure_vertical(session)
    p = await _ensure_pool(session)
    workflow = dict(SAFE_WORKFLOW)
    workflow["vertical_id"] = str(v.id)

    s = Strategy(
        name="Quickstart Strategy",
        vertical_id=v.id,
        status=StrategyStatusEnum.draft,
        owner_agent_id=owner_agent_id,
        summary="Starter strategy for quickstart run",
        tags=["quickstart"],
    )
    session.add(s)
    await session.flush()

    ver = StrategyVersion(
        strategy_id=s.id,
        semver="0.1.0",
        workflow_json=workflow,
        param_schema=None,
        changelog="Quickstart template",
        strategy_policy={"step_scorers": ["quality"], "record_quality_score": True},
    )
    session.add(ver)
    await session.flush()

    return QuickstartProvision(strategy_id=s.id, strategy_version_id=ver.id, pool_id=p.id)

