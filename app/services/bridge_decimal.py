"""ACP native 8 decimals ↔ wACP 18 decimals (see docs/bridge-spec-v1.md).

Cutover 2026-10-04: wrap ratio is **1 ACP ↔ 10 wACP** (not 1:1).
Decimal pad remains 10^(18-8); economic ratio multiplies on top.
"""
from __future__ import annotations

from decimal import Decimal

ACP_DECIMALS = 8
WACP_DECIMALS = 18
# Locked bridge doctrine — do not make env-tunable (avoids accidental drift).
WACP_PER_ACP = 10
_DECIMAL_PAD = Decimal(10) ** (WACP_DECIMALS - ACP_DECIMALS)  # 10^10
_SCALE = _DECIMAL_PAD * Decimal(WACP_PER_ACP)  # 10^11
# Pre-cutover scale (1 ACP ↔ 1 wACP) — accepted in reconciliation for legacy ops only.
_LEGACY_SCALE = _DECIMAL_PAD


def acp_smallest_to_wacp_wei(acp_smallest: int) -> int:
    if acp_smallest < 0:
        raise ValueError("acp_smallest must be non-negative")
    return acp_smallest * int(_SCALE)


def wacp_wei_to_acp_smallest_floor(wacp_wei: int) -> tuple[int, int]:
    """Return (acp_smallest_floor, remainder_wacp_wei) rounding down ACP payout."""
    if wacp_wei < 0:
        raise ValueError("wacp_wei must be non-negative")
    return divmod(wacp_wei, int(_SCALE))


def wacp_wei_to_acp_smallest_ceil(wacp_wei: int) -> int:
    """Return the ACP units required to fully back an aggregate wACP supply."""
    if wacp_wei < 0:
        raise ValueError("wacp_wei must be non-negative")
    scale = int(_SCALE)
    return (wacp_wei + scale - 1) // scale


def display_acp_from_smallest(acp_smallest: int) -> Decimal:
    return Decimal(acp_smallest) / (Decimal(10) ** ACP_DECIMALS)


def acp_usd_from_wacp_usd(wacp_usd: Decimal) -> Decimal:
    """USD spot for 1 ACP given wACP DEX USD (bridge 1 ACP = WACP_PER_ACP wACP)."""
    return Decimal(wacp_usd) * Decimal(WACP_PER_ACP)


def matches_recorded_wrap(acp_smallest: int, wacp_wei: int) -> bool:
    """True if amounts match current 10x ratio or legacy 1:1 pre-cutover mint."""
    if acp_smallest < 0 or wacp_wei < 0:
        return False
    expected_new = acp_smallest * int(_SCALE)
    expected_legacy = acp_smallest * int(_LEGACY_SCALE)
    return wacp_wei in (expected_new, expected_legacy)
