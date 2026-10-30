"""Unit tests for incremental ACP UTXO index (no live RPC)."""
from __future__ import annotations

from app.services import acp_utxo_index as idx
from app.services.acp_tokenomics import CUSTODIAL_HOT_ADDRESS, GENESIS_TREASURY_ADDRESS


def setup_function(_fn=None):
    with idx._lock:
        idx._state["wm"] = 0
        idx._state["tip_hash"] = None
        idx._state["unspent"] = {}
        idx._state["watch"] = {CUSTODIAL_HOT_ADDRESS, GENESIS_TREASURY_ADDRESS}
        idx._state["catchup_inflight"] = False


def test_apply_block_tracks_unspent_for_watched_addresses():
    unspent: dict[str, tuple[str, int]] = {}
    watch = {CUSTODIAL_HOT_ADDRESS, GENESIS_TREASURY_ADDRESS}
    block = {
        "tx": [
            {
                "txid": "aaaa",
                "vin": [],
                "vout": [
                    {"recipient_address": GENESIS_TREASURY_ADDRESS, "amount": 10},
                    {"recipient_address": CUSTODIAL_HOT_ADDRESS, "amount": 150_000_000},
                    {"recipient_address": "acp1qother00000000000000000000000000000000", "amount": 99},
                ],
            }
        ]
    }
    idx._apply_block(unspent, watch, block)
    assert unspent["aaaa:0"] == (GENESIS_TREASURY_ADDRESS, 10)
    assert unspent["aaaa:1"] == (CUSTODIAL_HOT_ADDRESS, 150_000_000)
    assert "aaaa:2" not in unspent

    spend = {
        "tx": [
            {
                "txid": "bbbb",
                "vin": [{"prev_txid": "aaaa", "vout": 1}],
                "vout": [{"recipient_address": CUSTODIAL_HOT_ADDRESS, "amount": 140_000_000}],
            }
        ]
    }
    idx._apply_block(unspent, watch, spend)
    assert "aaaa:1" not in unspent
    assert unspent["bbbb:0"] == (CUSTODIAL_HOT_ADDRESS, 140_000_000)


def test_unwatched_address_is_unknown_rather_than_zero(monkeypatch):
    from app.services import cache

    monkeypatch.setattr(cache, "cache_get_json_sync", lambda key: None)
    with idx._lock:
        idx._state["wm"] = 19
        idx._state["unspent"] = {"tx:0": (CUSTODIAL_HOT_ADDRESS, 100)}
    assert idx.get_indexed_balance("acp1qnewreserve") is None
    watched = idx.get_indexed_balance(GENESIS_TREASURY_ADDRESS)
    assert watched is not None
    assert watched["units"] == "0"


def test_amount_parser_rejects_ambiguous_decimal_strings():
    assert idx._amount_to_units(6_600_000_000) == 6_600_000_000
    try:
        idx._amount_to_units("66")
    except ValueError as exc:
        assert "integer" in str(exc)
    else:
        raise AssertionError("string RPC amount must be rejected")


def test_get_indexed_balance_after_seed_from_out_index():
    out_index = {
        ("tx1", 0): (GENESIS_TREASURY_ADDRESS, 207_643_979_999_999_800),
        ("tx2", 0): (CUSTODIAL_HOT_ADDRESS, 100_000_000_000_000),
    }
    idx.set_watch_addresses([GENESIS_TREASURY_ADDRESS, CUSTODIAL_HOT_ADDRESS])
    idx.seed_from_out_index(out_index, height=100)
    hot = idx.get_indexed_balance(CUSTODIAL_HOT_ADDRESS)
    assert hot is not None
    assert hot["utxo_count"] == 1
    assert hot["acp"].startswith("1000000")
    assert hot["source"] == "utxo_index"
    assert hot["chain_height"] == 100
    genesis = idx.get_indexed_balance(GENESIS_TREASURY_ADDRESS)
    assert genesis is not None
    assert genesis["utxo_count"] == 1


def test_advance_resets_stale_watermark_after_regenesis(monkeypatch):
    with idx._lock:
        idx._state["wm"] = 99
        idx._state["tip_hash"] = "old-tip"
        idx._state["unspent"] = {"old:0": (CUSTODIAL_HOT_ADDRESS, 999)}

    monkeypatch.setattr(idx, "_require_rpc_url", lambda: "http://node/rpc")

    def fake_rpc(_url, method, params=None):
        if method == "getblockcount":
            return 1
        if method == "getblockhash":
            assert params == {"height": 1}
            return "new-genesis"
        if method == "getblock":
            return {
                "tx": [
                    {
                        "txid": "genesis",
                        "vin": [],
                        "vout": [
                            {
                                "recipient_address": CUSTODIAL_HOT_ADDRESS,
                                "amount": 100_000_000,
                            }
                        ],
                    }
                ]
            }
        raise AssertionError(method)

    monkeypatch.setattr(idx, "_rpc", fake_rpc)
    result = idx.advance_index_sync(chunk=10)

    assert result["watermark"] == 1
    assert result["tip_hash"] == "new-genesis"
    assert "old:0" not in idx._state["unspent"]
    assert idx._state["unspent"]["genesis:0"] == (CUSTODIAL_HOT_ADDRESS, 100_000_000)
