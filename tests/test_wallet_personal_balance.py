"""Personal coins are visible; active platform claims cannot be spent twice."""
from decimal import Decimal as D

from app.api.routers.wallet_acp import _custodial_balance_view, _personal_balance_view


def test_personal_balance_does_not_hide_coins_or_cap_to_ledger():
    total, reserved, available = _personal_balance_view(D("1000666"), D("150600"), D("109093.96904092"))
    assert total == D("1000666")
    assert reserved == D("259693.96904092")
    assert available == D("740972.03095908")
    assert available < D("1000000")


def test_no_reservations_exposes_all_personal_coins():
    assert _personal_balance_view(D("1000666"), D(0), D(0)) == (D("1000666"), D(0), D("1000666"))


def test_insufficient_native_balance_never_goes_negative():
    assert _personal_balance_view(D(10), D(20), D(30)) == (D(10), D(50), D(0))


def test_shared_hot_balance_remains_capped_to_entitlement():
    assert _custodial_balance_view(D("1000000"), D(20), D(30)) == (D(50), D(50), D(30))
