"""Explicit EUR service pricing; independent of token market prices."""
import json
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

from app.config import get_settings

PRICES = json.loads(Path(__file__).with_name("catalog_eur_prices.json").read_text())
USD_PER_EUR_AT_CUTOVER = Decimal("1.1130")  # ECB, 2026-10-29; immutable migration rate.


def eur_sticker(amount: Decimal | str, *, catalog_slug: str | None = None) -> Decimal:
    if catalog_slug is not None:
        return Decimal(PRICES[catalog_slug])
    return (Decimal(str(amount)) / USD_PER_EUR_AT_CUTOVER).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def eur_to_acp(amount: Decimal | str) -> Decimal:
    value = Decimal(str(amount))
    if not value.is_finite() or value < 0:
        raise ValueError("Invalid EUR amount")
    return (value * get_settings().acp_per_eur).quantize(Decimal("0.01"), rounding=ROUND_CEILING)
