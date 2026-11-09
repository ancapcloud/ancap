"""rACP amount alignment helpers."""
from __future__ import annotations

import pytest

from app.services.racp_decimal import (
    RACP_WEI_PER_ACP,
    acp_smallest_to_racp_wei,
    is_redeemable_racp_wei,
    racp_wei_to_acp_smallest,
)


def test_ten_racp_maps_to_one_acp():
    assert racp_wei_to_acp_smallest(RACP_WEI_PER_ACP) == 100_000_000
    assert acp_smallest_to_racp_wei(100_000_000) == RACP_WEI_PER_ACP


def test_rejects_unaligned_wei():
    assert is_redeemable_racp_wei(1) is False
    with pytest.raises(ValueError):
        racp_wei_to_acp_smallest(1)


@pytest.mark.parametrize("sign", [1, -1])
def test_large_amount_formatting_preserves_digits_and_sign(sign):
    from app.services.racp_decimal import acp_smallest_to_decimal_str, racp_wei_to_human
    from decimal import Decimal, localcontext
    amount = sign * (10**60 + 12345678)
    with localcontext() as context:
        context.prec = 80
        expected_acp = format(Decimal(amount) / 10**8, "f")
        expected_racp = format(Decimal(amount) / 10**18, "f")
    with localcontext() as context:
        context.prec = 6
        assert acp_smallest_to_decimal_str(amount) == expected_acp
        assert racp_wei_to_human(amount) == expected_racp


def test_amount_formatting_keeps_existing_compact_output():
    from app.services.racp_decimal import acp_smallest_to_decimal_str
    assert acp_smallest_to_decimal_str(0) == "0"
    assert acp_smallest_to_decimal_str(10**8) == "1"
    assert acp_smallest_to_decimal_str(-1) == "-0.00000001"
