import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from eth_account import Account
from eth_account.messages import encode_typed_data
from fastapi import HTTPException
from app.services import racp_airdrop as service

POOL = "0x2867D10560b35616370cF5C7A21Ab1532698FD0F"
RECIPIENT = "0x0000000000000000000000000000000000001234"


def test_voucher_is_bound_to_wallet_account_chain_and_contract(monkeypatch, tmp_path):
    key = Account.create()
    key_file = tmp_path / "signer.key"
    key_file.write_text(key.key.hex())
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(racp_airdrop_signer_file=str(key_file)))
    monkeypatch.setattr(service, "campaign_config", lambda: {"contract": POOL})
    monkeypatch.setattr(service, "chain_state", AsyncMock(return_value={"claimed": False, "identity_claimed": False, "paused": False, "balance": service.BUDGET_WEI, "distributed": 0, "signer": key.address}))
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: SimpleNamespace(wallet_address=RECIPIENT))))
    voucher = asyncio.run(service.issue_voucher(session, "private-account-id", RECIPIENT))
    message = service.typed_claim(POOL, voucher.recipient, voucher.eligibility_id, voucher.deadline)
    assert Account.recover_message(encode_typed_data(full_message=message), signature=voucher.signature) == key.address
    message["domain"]["chainId"] = 56
    assert Account.recover_message(encode_typed_data(full_message=message), signature=voucher.signature) != key.address
    assert "private-account-id" not in voucher.model_dump_json()
    assert voucher.grant == "500"


def test_unlinked_wallet_cannot_obtain_voucher():
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.issue_voucher(session, "user", RECIPIENT))
    assert exc.value.status_code == 403


@pytest.mark.parametrize("state", [
    {"claimed": True, "identity_claimed": False, "paused": False, "balance": service.BUDGET_WEI, "distributed": 0},
    {"claimed": False, "identity_claimed": True, "paused": False, "balance": service.BUDGET_WEI, "distributed": 0},
    {"claimed": False, "identity_claimed": False, "paused": True, "balance": service.BUDGET_WEI, "distributed": 0},
    {"claimed": False, "identity_claimed": False, "paused": False, "balance": service.GRANT_WEI-1, "distributed": 0},
])
def test_claimed_paused_and_insufficient_campaigns_fail_closed(monkeypatch, state):
    monkeypatch.setattr(service, "campaign_config", lambda: {"contract": POOL})
    monkeypatch.setattr(service, "chain_state", AsyncMock(return_value=state))
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: SimpleNamespace(wallet_address=RECIPIENT))))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.issue_voucher(session, "user", RECIPIENT))
    assert exc.value.status_code == 409
