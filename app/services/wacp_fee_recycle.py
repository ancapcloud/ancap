"""Fee → wrap → V3 top-up eligibility (operator cadence, not auto-mint)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.market_economy import OFFICIAL_WACP_POOL_V3, _configured_v3_pool


def _to_dec(raw: Any) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid revenue or threshold") from exc
    if not value.is_finite() or value < 0:
        raise ValueError("Revenue and threshold must be finite and non-negative")
    return value


def _revenue_from_status(status: Any) -> Decimal:
    ledger = status.get("ledger") if isinstance(status, dict) else getattr(status, "ledger", None)
    raw = ledger.get("revenue_30d") if isinstance(ledger, dict) else getattr(ledger, "revenue_30d", None)
    # A zero 30-day window is authoritative, never replaced with historical revenue.
    return _to_dec(raw)


async def fee_recycle_eligibility(session: AsyncSession) -> dict[str, Any]:
    """Go/no-go for weekly platform-fee recycling into the bootstrap V3 pool.

    Does not move funds — operator signs wrap + LP after a pass.
    """
    from app.services.project_treasury import treasury_status

    s = get_settings()
    status = await treasury_status(session)
    invalid = False
    try:
        min_rev = _to_dec(getattr(s, "wacp_fee_recycle_min_revenue_acp", "50"))
        if min_rev <= 0:
            raise ValueError("Threshold must be positive")
        revenue = _revenue_from_status(status)
    except ValueError:
        invalid = True
        min_rev, revenue = Decimal("0"), Decimal("0")
    pool = (s.wacp_v3_pool or "").strip().lower() or _configured_v3_pool() or OFFICIAL_WACP_POOL_V3
    oracle_use_v3 = bool(getattr(s, "wacp_oracle_use_v3", False))
    eligible = not invalid and revenue >= min_rev

    reasons: list[str] = []
    if invalid:
        reasons.append("Invalid or missing 30-day revenue / positive threshold; no eligibility approval")
    elif not eligible:
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
        "min_revenue_acp": None if invalid else format(min_rev, "f"),
        "revenue_window": "30d",
        "input_valid": not invalid,
        "v3_pool": pool,
        "oracle_use_v3": oracle_use_v3,
        "action": (
            "Approve fee tranche → wrap wACP → Add Liquidity on V3 (human-signed). "
            "Do not mint to the pool. Do not wash trade."
        ),
        "reasons": reasons,
        "playbook": "docs/WACP_LIQUIDITY_V3_PLAYBOOK.md § fee recycling",
    }
