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
