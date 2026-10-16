"""Read-only chain/supply acceptance check for primary, Oracle and local ACP peers."""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import requests


DEFAULT_PEERS = [
    "https://acp1.ancap.cloud/rpc",
    "http://152.67.79.206:8545/rpc",
    "http://127.0.0.1:8545/rpc",
]


def inspect_peer(url: str) -> dict:
    def rpc(method: str):
        response = requests.post(url, json={
            "jsonrpc": "2.0", "id": 1, "method": method, "params": [],
        }, timeout=15)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise ValueError(f"{method}: {payload['error']}")
        return payload["result"]

    try:
        height = rpc("getblockcount")
        block_hash = rpc("getbestblockhash")
        supply = rpc("gettxoutsetinfo")
        return {"peer": url, "height": height, "tip": block_hash, "supply": supply}
    except Exception as error:
        return {"peer": url, "error": str(error)}


def peers_agree(results: list[dict]) -> bool:
    if not results or any("error" in row for row in results):
        return False
    expected = (results[0]["height"], results[0]["tip"])
    cap = "21000000000000000"
    for row in results:
        supply = row["supply"]
        if (row["height"], row["tip"]) != expected:
            return False
        if not supply.get("initialized") or supply.get("supply_invariant_ok") is not True:
            return False
        if supply.get("height") != row["height"]:
            return False
        if str(supply.get("issued_supply_units")) != cap or str(supply.get("max_supply_units")) != cap:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--peer", action="append", help="RPC URL; repeat to override the three defaults")
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(inspect_peer, args.peer or DEFAULT_PEERS))
    ok = peers_agree(results)
    print(json.dumps({"ok": ok, "peers": results}, indent=2, ensure_ascii=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
