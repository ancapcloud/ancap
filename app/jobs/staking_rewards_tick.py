from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import PLATFORM_ACCOUNT_OWNER_ID
from app.db.models import JobWatermark, LedgerEvent, LedgerEventTypeEnum, Stake, StakeStatusEnum
from app.services.ledger import append_event, get_or_create_account

WM_LAST_DAY_KEY = "staking_rewards:last_day"
WM_EMISSION_USED_KEY = "staking_rewards:bootstrap_emission_used"
Q = Decimal("0.00000001")


def _d(value: str | Decimal | None, fallback: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value is not None else fallback))
    except Exception:
        return Decimal(fallback)


async def staking_rewards_tick(session: AsyncSession) -> dict:
    s = get_settings()
    if not s.staking_rewards_enabled:
        return {"enabled": False, "skipped": True, "reason": "disabled"}

    today = datetime.now(timezone.utc).date().isoformat()
    last_day = (
        await session.execute(select(JobWatermark.value).where(JobWatermark.key == WM_LAST_DAY_KEY).limit(1))
    ).scalar_one_or_none()
    if last_day == today:
        return {"enabled": True, "skipped": True, "reason": "already_processed", "day": today}

    currency = (s.staking_rewards_currency or "ACP").upper()
    min_stake = _d(s.staking_rewards_min_stake_for_rewards, "25")
    floor_pct = _d(s.staking_rewards_apy_floor_percent, "3")
    cap_pct = _d(s.staking_rewards_apy_ceiling_percent, "18")
    fees_share = _d(s.staking_rewards_fees_share_percent, "40") / Decimal("100")
    slash_share = _d(s.staking_rewards_slash_share_percent, "100") / Decimal("100")
    emission_daily = _d(s.staking_rewards_bootstrap_daily_emission, "300")
    emission_cap = _d(s.staking_rewards_bootstrap_emission_cap_total, "108000")

    active_rows = (
        await session.execute(
            select(Stake.agent_id, func.sum(Stake.amount_value))
            .where(
                Stake.status == StakeStatusEnum.active,
                Stake.amount_currency == currency,
            )
            .group_by(Stake.agent_id)
        )
    ).all()
    agent_weights: list[tuple[UUID, Decimal]] = []
    total_weight = Decimal("0")
    for agent_id, amount in active_rows:
        v = _d(amount)
        if v >= min_stake:
            agent_weights.append((UUID(str(agent_id)), v))
            total_weight += v

    if total_weight <= 0 or not agent_weights:
        stmt = insert(JobWatermark).values(key=WM_LAST_DAY_KEY, value=today)
        stmt = stmt.on_conflict_do_update(index_elements=["key"], set_={"value": today, "updated_at": func.now()})
        await session.execute(stmt)
        return {"enabled": True, "skipped": True, "reason": "no_eligible_stakes", "day": today}

    since = datetime.now(timezone.utc) - timedelta(days=1)
    fee_sum = (
        await session.execute(
            select(func.coalesce(func.sum(LedgerEvent.amount_value), 0)).where(
                LedgerEvent.type == LedgerEventTypeEnum.fee,
                LedgerEvent.amount_currency == currency,
                LedgerEvent.ts >= since,
            )
        )
    ).scalar_one()
    slash_sum = (
        await session.execute(
            select(func.coalesce(func.sum(LedgerEvent.amount_value), 0)).where(
                LedgerEvent.type == LedgerEventTypeEnum.slash,
                LedgerEvent.amount_currency == currency,
                LedgerEvent.ts >= since,
            )
        )
    ).scalar_one()

    fees_component = (_d(fee_sum) * fees_share).quantize(Q, rounding=ROUND_DOWN)
    slash_component = (_d(slash_sum) * slash_share).quantize(Q, rounding=ROUND_DOWN)
    base_rewards = fees_component + slash_component

    emission_used_raw = (
        await session.execute(select(JobWatermark.value).where(JobWatermark.key == WM_EMISSION_USED_KEY).limit(1))
    ).scalar_one_or_none()
    emission_used = _d(emission_used_raw, "0")
    emission_left = max(Decimal("0"), emission_cap - emission_used)
    emission_component = Decimal("0")

    annualized_base = base_rewards * Decimal("365") / total_weight * Decimal("100")
    if annualized_base < floor_pct and emission_left > 0:
        floor_daily_target = (total_weight * floor_pct / Decimal("100")) / Decimal("365")
        needed = max(Decimal("0"), floor_daily_target - base_rewards)
        emission_component = min(emission_daily, emission_left, needed).quantize(Q, rounding=ROUND_DOWN)

    rewards_gross = base_rewards + emission_component
    ceiling_daily_target = (total_weight * cap_pct / Decimal("100")) / Decimal("365")
    rewards_paid = min(rewards_gross, ceiling_daily_target).quantize(Q, rounding=ROUND_DOWN)
    overflow_to_treasury = max(Decimal("0"), rewards_gross - rewards_paid).quantize(Q, rounding=ROUND_DOWN)

    if rewards_paid > 0:
        acc_platform = await get_or_create_account(session, "system", PLATFORM_ACCOUNT_OWNER_ID)
        distributed = Decimal("0")
        for idx, (agent_id, weight) in enumerate(agent_weights):
            if idx == len(agent_weights) - 1:
                reward = (rewards_paid - distributed).quantize(Q, rounding=ROUND_DOWN)
            else:
                reward = (rewards_paid * weight / total_weight).quantize(Q, rounding=ROUND_DOWN)
            distributed += reward
            if reward <= 0:
                continue
            acc_agent = await get_or_create_account(session, "agent", agent_id)
            await append_event(
                session,
                LedgerEventTypeEnum.transfer,
                currency,
                reward,
                src_account_id=acc_platform.id,
                dst_account_id=acc_agent.id,
                metadata={
                    "type": "staking_reward",
                    "day": today,
                    "agent_id": str(agent_id),
                    "components": {
                        "fees": str(fees_component),
                        "slashes": str(slash_component),
                        "emission": str(emission_component),
                    },
                },
            )

    new_emission_used = (emission_used + emission_component).quantize(Q, rounding=ROUND_DOWN)
    for k, v in ((WM_LAST_DAY_KEY, today), (WM_EMISSION_USED_KEY, str(new_emission_used))):
        stmt = insert(JobWatermark).values(key=k, value=v)
        stmt = stmt.on_conflict_do_update(index_elements=["key"], set_={"value": v, "updated_at": func.now()})
        await session.execute(stmt)

    annualized_paid = (rewards_paid * Decimal("365") / total_weight * Decimal("100")).quantize(Q, rounding=ROUND_DOWN)
    return {
        "enabled": True,
        "day": today,
        "eligible_agents": len(agent_weights),
        "eligible_staked_total": str(total_weight),
        "components": {
            "fees": str(fees_component),
            "slashes": str(slash_component),
            "emission": str(emission_component),
            "overflow_to_treasury": str(overflow_to_treasury),
        },
        "rewards_paid_total": str(rewards_paid),
        "annualized_apy_percent": str(annualized_paid),
        "bootstrap_emission_used_total": str(new_emission_used),
    }
