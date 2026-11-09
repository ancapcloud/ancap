from decimal import Decimal

from app.services.bridge_decimal import (
    WACP_PER_ACP,
    acp_smallest_to_wacp_wei,
    acp_usd_from_wacp_usd,
    display_acp_from_smallest,
    matches_recorded_wrap,
    wacp_wei_to_acp_smallest_ceil,
    wacp_wei_to_acp_smallest_floor,
)


def test_wrap_ratio_locked():
    assert WACP_PER_ACP == 10


def test_acp_to_wacp_roundtrip_floor():
    s = 100_000_000  # 1 ACP in smallest
    w = acp_smallest_to_wacp_wei(s)
    assert w == 10 * 10**18  # 10 wACP
    back, rem = wacp_wei_to_acp_smallest_floor(w)
    assert back == s
    assert rem == 0


def test_remainder_on_partial_wei():
    # 10 wACP + dust wei
    w = 10 * 10**18 + 123
    back, rem = wacp_wei_to_acp_smallest_floor(w)
    assert rem == 123
    assert back == 10**8
    assert wacp_wei_to_acp_smallest_ceil(w) == 10**8 + 1


def test_legacy_and_new_wrap_match():
    s = 100_000_000
    assert matches_recorded_wrap(s, 10 * 10**18)  # new
    assert matches_recorded_wrap(s, 10**18)  # legacy 1:1
    assert not matches_recorded_wrap(s, 2 * 10**18)


def test_acp_usd_from_wacp():
    assert acp_usd_from_wacp_usd(Decimal("0.001")) == Decimal("0.010")


def test_display():
    assert display_acp_from_smallest(1) == Decimal("0.00000001")


def test_uint256_scale_conversion_preserves_dust_and_integer_types():
    wei = 2**256 - 1
    smallest, dust = wacp_wei_to_acp_smallest_floor(wei)
    assert type(smallest) is int and type(dust) is int
    assert 0 <= dust < 10**11
    assert acp_smallest_to_wacp_wei(smallest) + dust == wei
    assert wacp_wei_to_acp_smallest_ceil(wei) == smallest + 1
    assert matches_recorded_wrap(smallest, smallest * 10**11)
    assert matches_recorded_wrap(smallest, smallest * 10**10)
