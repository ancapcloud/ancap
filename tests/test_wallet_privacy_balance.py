import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from app.api.routers import wallet_acp as wallet


@pytest.mark.parametrize('deposit,privacy,stake,ledger,expected', [
    ('0', '100', '0', '0', '100'),
    ('10', '100', '20', '30', '60'),
    ('10', None, '0', '0', '0'),
])
def test_privacy_coins_preserve_reservations_and_show_total(monkeypatch, deposit, privacy, stake, ledger, expected):
    monkeypatch.setattr(wallet, '_in_work_breakdown_for_user', AsyncMock(return_value=(Decimal(stake) + Decimal(ledger), Decimal(stake), Decimal(ledger))))
    monkeypatch.setattr(wallet, 'user_is_custodial_hot_holder', AsyncMock(return_value=False))
    monkeypatch.setattr(wallet, '_privacy_receive_snapshot', AsyncMock(return_value=(None if privacy is None else Decimal(privacy), [])))
    monkeypatch.setattr(wallet, '_creator_vesting_snapshot', lambda address: None)
    result = asyncio.run(wallet._decorate_balance_for_user(None, 'owner', {
        'address': 'acp1personal', 'acp': deposit, 'utxo_count': 1,
    }, include_in_work=True))
    assert Decimal(result.withdrawable_now_acp) == Decimal(expected)
    assert Decimal(result.primary_acp) == Decimal(deposit) + Decimal(privacy or '0')
    if privacy is None:
        assert result.probe_status == 'degraded'
