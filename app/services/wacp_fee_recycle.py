"""Fee → wrap → V3 top-up eligibility (operator cadence, not auto-mint)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.market_economy import OFFICIAL_WACP_POOL_V3, _configured_v3_pool


def _to_dec(raw: Any) -> Decimal:
    try:
        return Decimal(str(raw or "0"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _revenue_from_status(status: Any) -> Decimal:
    ledger = getattr(status, "ledger", None)
    if ledger is not None:
        for attr in ("revenue_30d", "revenue_total"):
            val = _to_dec(getattr(ledger, attr, None))
            if val > 0:
                return val
    if isinstance(status, dict):
        nested = status.get("ledger") or {}
        for key in ("revenue_30d", "revenue_total"):
            val = _to_dec(nested.get(key) if isinstance(nested, dict) else None)
            if val > 0:
                return val
    return Decimal("0")


async def fee_recycle_eligibility(session: AsyncSession) -> dict[str, Any]:
    """Go/no-go for weekly platform-fee recycling into the bootstrap V3 pool.

    Does not move funds — operator signs wrap + LP after a pass.
    """
    from app.services.project_treasury import treasury_status

    s = get_settings()
    min_rev = _to_dec(getattr(s, "wacp_fee_recycle_min_revenue_acp", None) or "50")
    status = await treasury_status(session)
    revenue = _revenue_from_status(status)
    pool = (s.wacp_v3_pool or "").strip().lower() or _configured_v3_pool() or OFFICIAL_WACP_POOL_V3
    oracle_use_v3 = bool(getattr(s, "wacp_oracle_use_v3", False))
    eligible = revenue >= min_rev

    reasons: list[str] = []
    if not eligible:
        reasons.append(
            f"ledger revenue {revenue} ACP < min {min_rev} ACP — grow platform spend first"
        )
    else:
        reasons.append("revenue threshold met — operator may wrap an approved fee tranche into V3")

    if oracle_use_v3:
        reasons.append("oracle already on V3 — recycle still allowed; watch slippage")
    else:
        reasons.append("oracle remains on V2 reference (WACP_ORACLE_USE_V3=false) — correct for shallow V3")

    return {
        "eligible": eligible,
        "ledger_revenue_acp": format(revenue, "f"),
        "min_revenue_acp": format(min_rev, "f"),
        "v3_pool": pool,
        "oracle_use_v3": oracle_use_v3,
        "action": (
            "Approve fee tranche → wrap wACP → Add Liquidity on V3 (human-signed). "
            "Do not mint to the pool. Do not wash trade."
        ),
        "reasons": reasons,
        "playbook": "docs/WACP_LIQUIDITY_V3_PLAYBOOK.md § fee recycling",
    }
