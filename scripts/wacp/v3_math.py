"""Planning math for PancakeSwap V3 concentrated liquidity (human-readable units).

Production on-chain minting must use PancakeSwap TickMath / SDK integers.
This module uses float/Decimal for operator planning and CI golden tests.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

BASE = 1.0001


def human_to_raw_price(price_human: float, token0_decimals: int, token1_decimals: int) -> float:
    return price_human * (10**token1_decimals) / (10**token0_decimals)


def price_to_raw_tick(price_raw: float) -> float:
    if price_raw <= 0:
        raise ValueError("price_raw must be positive")
    return math.log(price_raw) / math.log(BASE)


def snap_ticks(raw_low: float, raw_high: float, spacing: int) -> tuple[int, int]:
    if spacing <= 0:
        raise ValueError("tickSpacing must be positive")
    tick_low = int(math.floor(raw_low / spacing) * spacing)
    tick_high = int(math.ceil(raw_high / spacing) * spacing)
    if tick_low >= tick_high:
        raise ValueError("Invalid snapped tick range")
    return tick_low, tick_high


def raw_price_at_tick(tick: int) -> float:
    return BASE**tick


def sqrt_price_from_raw(price_raw: float) -> float:
    return math.sqrt(price_raw)


def liquidity_from_token0(amount0: float, sqrt_p: float, sqrt_b: float) -> float:
    if sqrt_b <= sqrt_p:
        raise ValueError("sqrt_b must exceed sqrt_p for in-range token0 deposit")
    return amount0 * sqrt_p * sqrt_b / (sqrt_b - sqrt_p)


def token1_from_liquidity(L: float, sqrt_a: float, sqrt_p: float) -> float:
    if sqrt_p <= sqrt_a:
        raise ValueError("sqrt_p must exceed sqrt_a for token1 side")
    return L * (sqrt_p - sqrt_a)


@dataclass
class V3DeployPlan:
    p0_human: float
    range_fraction: float
    tick_lower: int
    tick_upper: int
    amount0: float
    amount1: float
    liquidity: float
    usdt_required: float


def deploy_from_wacp_amount(
    wacp_amount: float,
    p0_usdt_per_wacp: float,
    range_fraction: float,
    tick_spacing: int,
    *,
    token0_decimals: int = 18,
    token1_decimals: int = 18,
    wacp_is_token0: bool = True,
) -> V3DeployPlan:
    """Mode B1: fixed wACP (token0) budget at center price."""
    if not wacp_is_token0:
        raise NotImplementedError("token1=wACP planning path: swap token roles in CLI")

    p_low = p0_usdt_per_wacp * (1.0 - range_fraction)
    p_high = p0_usdt_per_wacp * (1.0 + range_fraction)

    p0_raw = human_to_raw_price(p0_usdt_per_wacp, token0_decimals, token1_decimals)
    p_low_raw = human_to_raw_price(p_low, token0_decimals, token1_decimals)
    p_high_raw = human_to_raw_price(p_high, token0_decimals, token1_decimals)

    raw_low = price_to_raw_tick(p_low_raw)
    raw_high = price_to_raw_tick(p_high_raw)
    tick_lower, tick_upper = snap_ticks(raw_low, raw_high, tick_spacing)

    sa = sqrt_price_from_raw(raw_price_at_tick(tick_lower))
    sb = sqrt_price_from_raw(raw_price_at_tick(tick_upper))
    sp = sqrt_price_from_raw(p0_raw)

    L = liquidity_from_token0(wacp_amount, sp, sb)
    usdt = token1_from_liquidity(L, sa, sp)

    return V3DeployPlan(
        p0_human=p0_usdt_per_wacp,
        range_fraction=range_fraction,
        tick_lower=tick_lower,
        tick_upper=tick_upper,
        amount0=wacp_amount,
        amount1=usdt,
        liquidity=L,
        usdt_required=usdt,
    )


def deploy_from_usdt_budget(
    usdt_budget: float,
    p0_usdt_per_wacp: float,
    range_fraction: float,
    tick_spacing: int,
    *,
    token0_decimals: int = 18,
    token1_decimals: int = 18,
) -> V3DeployPlan:
    """Mode B2: fixed USDT budget at center price."""
    p_low = p0_usdt_per_wacp * (1.0 - range_fraction)
    p_high = p0_usdt_per_wacp * (1.0 + range_fraction)

    p0_raw = human_to_raw_price(p0_usdt_per_wacp, token0_decimals, token1_decimals)
    p_low_raw = human_to_raw_price(p_low, token0_decimals, token1_decimals)
    p_high_raw = human_to_raw_price(p_high, token0_decimals, token1_decimals)

    raw_low = price_to_raw_tick(p_low_raw)
    raw_high = price_to_raw_tick(p_high_raw)
    tick_lower, tick_upper = snap_ticks(raw_low, raw_high, tick_spacing)

    sa = sqrt_price_from_raw(raw_price_at_tick(tick_lower))
    sb = sqrt_price_from_raw(raw_price_at_tick(tick_upper))
    sp = sqrt_price_from_raw(p0_raw)

    denom = p0_usdt_per_wacp * (sb - sp) / (sp * sb) + (sp - sa)
    if denom <= 0:
        raise ValueError("invalid range for USDT budget solve")
    L = usdt_budget / denom
    amount0 = L * (sb - sp) / (sp * sb)
    amount1 = L * (sp - sa)

    return V3DeployPlan(
        p0_human=p0_usdt_per_wacp,
        range_fraction=range_fraction,
        tick_lower=tick_lower,
        tick_upper=tick_upper,
        amount0=amount0,
        amount1=amount1,
        liquidity=L,
        usdt_required=amount1,
    )


def acp_smallest_to_wacp_human(acp_smallest: int) -> Decimal:
    """8-dec ACP smallest → human wACP at bridge ratio 1 ACP = 10 wACP."""
    from app.services.bridge_decimal import WACP_PER_ACP

    return (Decimal(acp_smallest) / Decimal(10**8)) * Decimal(WACP_PER_ACP)
