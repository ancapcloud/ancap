"""rACP ↔ ACP amount math. Contract: 1 ACP = 10 rACP; amount % 10^11 == 0."""
from __future__ import annotations

from decimal import Decimal

RACP_PER_ACP = 10
RACP_DECIMALS = 18
ACP_DECIMALS = 8
# Wei per native ACP unit (10 rACP * 10^18 / 10^8 = 10^11).
RACP_WEI_PER_ACP_SMALLEST = 10**11
RACP_WEI_PER_ACP = RACP_PER_ACP * (10**RACP_DECIMALS)


def is_redeemable_racp_wei(amount_racp_wei: int) -> bool:
    return int(amount_racp_wei) > 0 and int(amount_racp_wei) % RACP_WEI_PER_ACP_SMALLEST == 0


def racp_wei_to_acp_smallest(amount_racp_wei: int) -> int:
    amount = int(amount_racp_wei)
    if not is_redeemable_racp_wei(amount):
        raise ValueError("rACP amount is not aligned to native ACP 8-decimal units")
    return amount // RACP_WEI_PER_ACP_SMALLEST


def acp_smallest_to_racp_wei(amount_acp_smallest: int) -> int:
    amount = int(amount_acp_smallest)
    if amount <= 0:
        raise ValueError("ACP amount must be positive")
    return amount * RACP_WEI_PER_ACP_SMALLEST


def acp_smallest_to_decimal_str(amount_acp_smallest: int) -> str:
    return format(Decimal(int(amount_acp_smallest)) / (Decimal(10) ** ACP_DECIMALS), "f")


def racp_wei_to_human(amount_racp_wei: int) -> str:
    return format(Decimal(int(amount_racp_wei)) / (Decimal(10) ** RACP_DECIMALS), "f")
