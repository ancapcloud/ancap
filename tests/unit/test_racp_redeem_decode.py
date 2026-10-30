"""RedemptionRequested log decode + ACP destination validation."""
from __future__ import annotations

from eth_abi import encode
from eth_utils import keccak

from app.services.racp_redeem_watcher import decode_redemption_requested, is_valid_acp_destination

TOPIC0 = "0x" + keccak(text="RedemptionRequested(uint256,address,uint256,string)").hex()


def test_is_valid_acp_destination():
    assert is_valid_acp_destination("acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz")
    assert not is_valid_acp_destination("0xabc")
    assert not is_valid_acp_destination("")


def test_decode_redemption_requested():
    amount = 10 * 10**18
    acp = "acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz"
    holder = "0x" + "11" * 20
    data = "0x" + encode(["uint256", "string"], [amount, acp]).hex()
    log = {
        "topics": [
            TOPIC0,
            "0x" + (42).to_bytes(32, "big").hex(),
            "0x" + ("0" * 24) + holder[2:],
        ],
        "data": data,
        "transactionHash": "0x" + "ab" * 32,
        "blockNumber": "0x10",
        "logIndex": "0x1",
    }
    decoded = decode_redemption_requested(log)
    assert decoded is not None
    assert decoded["redemption_id"] == 42
    assert decoded["holder"] == holder.lower()
    assert decoded["amount"] == amount
    assert decoded["acp_address"] == acp
    assert decoded["log_index"] == 1
