"""L3: Self-evolution — auto-adjust risk limits from reputation (trust_score)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TrustScore, RiskPolicy


async def auto_limits_tick(session: AsyncSession, *, window: str = "90d", max_updates: int = 100) -> int:
    """
    For each agent with a trust_score, upsert risk_policies (e.g. max_runs_per_day) scaled by score.
    Returns number of policies updated/created.
    """
    r = await session.execute(
        select(TrustScore)
        .where(TrustScore.window == window)
        .order_by(TrustScore.computed_at.desc())
        .limit(max_updates * 2)
    )
    scores = r.scalars().all()
    # Dedupe by subject (keep latest)
    seen = set()
    updates = 0
    for ts in scores:
        key = (ts.subject_type, str(ts.subject_id))
        if key in seen:
            continue
        seen.add(key)
        if ts.subject_type != "agent":
            continue
        # Scale: trust 0.5 -> base limits, 1.0 -> 2x, 0.0 -> 0.5x
        scale = 0.5 + float(ts.trust_score)
        max_runs = max(1, int(10 * scale))
        policy_json = {"max_runs_per_day": max_runs, "source": "auto_limits", "trust_score": float(ts.trust_score)}
        existing = await session.execute(
            select(RiskPolicy).where(
                RiskPolicy.scope_type == "agent",
                RiskPolicy.scope_id == ts.subject_id,
            ).limit(1)
        )
        pol = existing.scalar_one_or_none()
        if pol:
            pol.policy_json = policy_json
            updates += 1
        else:
            session.add(RiskPolicy(scope_type="agent", scope_id=ts.subject_id, policy_json=policy_json))
            updates += 1
        if updates >= max_updates:
            break
    return updates
