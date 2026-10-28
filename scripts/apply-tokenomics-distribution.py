#!/usr/bin/env python3
"""Apply official tokenomics UTXO distribution from genesis treasury.

Preserves: bridge reserve, user genesis wallets (5020 ACP), project treasury (miner).
Validator reserve: receives genesis remainder after Creator/Public/Ecosystem full targets.
Does NOT sweep custodial hot (user wallet) except optional explicit remainder pass.
"""
from __future__ import annotations
from pathlib import Path

import json
import os
import subprocess
import sys
import time

RPC = os.environ.get("ACP_RPC_URL", "http://acp-node:8545/rpc")
WALLETD = os.environ.get("ACP_WALLETD_PATH", "walletd")
GENESIS_KS = os.environ.get(
    "GENESIS_KEYSTORE_FILE", "/run/secrets/genesis-v2/genesis-treasury.keystore.json"
)

# Official tokenomics (protocol_params.rs)
CREATOR = ("creator", "acp1qrfw3d50jd4864vxhatuknhw65jwv463ccr6flsl", 69_300_000)
VALIDATOR = ("validator", "acp1qp69rhaq4k8lgfwdqynqq5uva7uvswne8qq6g5um", 105_000_000)
PUBLIC = ("public", "acp1qqla8waukrudkleau9n6gzj9c58ufyfxaulvwumm", 25_200_000)
ECOSYSTEM = ("ecosystem", "acp1qq9t4lf4z7lprt7a6nr682cl02f5tcyh45stakdf", 10_500_000)
HOT = ("hot", "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9", None)

# Do not touch these (user + bridge + miner)
PROTECTED = {
    "acp1qz06ucs5zemu8mrdftp5gg8ckmevks0wqvhek4wa",  # user 5000
    "acp1qrtuzja28v72gera5s45h3ltxcxhvzqa2vmxhkhw",  # user 10
    "acp1qq69wvq2f0f0gk9tmezvtxtfmu946vgcpc5dlm8x",  # user 10
    "acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz",  # bridge reserve
    "acp1qpw9nstpx5vtmqxdxmmud25dk0ae4s6a7cs7n902",  # project treasury / miner
}


def walletd(args: list[str]) -> dict:
    r = subprocess.run([WALLETD, *args], capture_output=True, text=True, timeout=180)
    out = (r.stdout or "").strip()
    payload = json.loads(out) if out else {}
    if r.returncode != 0 or not payload.get("ok"):
        raise RuntimeError(payload.get("error") or r.stderr or "walletd failed")
    return payload["result"]


def acp_units(s: str) -> float:
    return float(s.replace(",", ""))


def transfer_ks(ks_path: str, to: str, amount_acp: str, use_json: bool = False) -> dict:
    if use_json:
        ks = Path(ks_path).read_text(encoding='utf-8')
        args = ["transfer", "--rpc", RPC, "--keystore-json", ks, "--to", to, "--amount-acp", amount_acp]
    else:
        args = ["transfer", "--rpc", RPC, "--keystore-file", ks_path, "--to", to, "--amount-acp", amount_acp]
    return walletd(args)


def fmt_acp(units: int) -> str:
    whole = units // 100_000_000
    frac = units % 100_000_000
    return f"{whole}.{frac:08d}".rstrip("0").rstrip(".")


def main() -> int:
    if not os.path.isfile(GENESIS_KS):
        print(f"Missing genesis keystore: {GENESIS_KS}", file=sys.stderr)
        return 1

    derived = walletd(["address", "--keystore-file", GENESIS_KS])["address"]
    print(f"Genesis signer: {derived}")

    gb = walletd(["balance", "--rpc", RPC, "--address", derived])
    genesis_acp = acp_units(gb["acp"])
    print(f"Genesis balance before: {gb['acp']} ACP")

    if genesis_acp < 1_000_000:
        print("Genesis treasury too low; already distributed?", file=sys.stderr)
        return 1

    # Full targets for creator / public / ecosystem; validator gets the rest.
    plan: list[tuple[str, str, str]] = []
    for label, addr, target in (CREATOR, PUBLIC, ECOSYSTEM):
        bal = walletd(["balance", "--rpc", RPC, "--address", addr])
        cur = acp_units(bal["acp"])
        need = max(0.0, float(target) - cur)
        if need >= 0.000001:
            # leave 1 smallest fee headroom in string formatting
            amt = f"{need:.8f}".rstrip("0").rstrip(".")
            plan.append((label, addr, amt))
            print(f"Plan {label}: send {amt} ACP -> {addr} (target {target})")

    reserved = 69_300_000 + 25_200_000 + 10_500_000
    if genesis_acp < reserved - 1:
        print(
            f"WARNING: genesis {genesis_acp} < {reserved} needed for full Creator+Public+Ecosystem",
            file=sys.stderr,
        )

    for label, addr, amt in plan:
        print(f"=== {label}: {amt} ACP ===")
        res = transfer_ks(GENESIS_KS, addr, amt)
        print(json.dumps(res))
        if not res.get("accepted"):
            print(f"FAILED {label}", file=sys.stderr)
            return 1
        time.sleep(8)

    # Validator: remainder on genesis treasury (up to 105M target)
    gb2 = walletd(["balance", "--rpc", RPC, "--address", derived])
    rem = acp_units(gb2["acp"])
    vb = walletd(["balance", "--rpc", RPC, "--address", VALIDATOR[1]])
    vcur = acp_units(vb["acp"])
    vneed = min(rem - 0.000001, max(0.0, float(VALIDATOR[2]) - vcur))
    if vneed >= 0.000001:
        amt = f"{vneed:.8f}".rstrip("0").rstrip(".")
        print(f"=== validator remainder: {amt} ACP (target {VALIDATOR[2]}) ===")
        res = transfer_ks(GENESIS_KS, VALIDATOR[1], amt)
        print(json.dumps(res))
        if not res.get("accepted"):
            print("Validator transfer failed", file=sys.stderr)
            return 1
        time.sleep(8)

    # Any dust left on genesis -> hot (operator remainder), if env set
    hot_remainder = os.environ.get("SEND_GENESIS_DUST_TO_HOT", "1") == "1"
    gb3 = walletd(["balance", "--rpc", RPC, "--address", derived])
    rem3 = acp_units(gb3["acp"])
    if hot_remainder and rem3 > 0.000002:
        amt = f"{rem3 - 0.000001:.8f}".rstrip("0").rstrip(".")
        if acp_units(amt) > 0:
            print(f"=== genesis dust -> hot: {amt} ACP ===")
            res = transfer_ks(GENESIS_KS, HOT[1], amt)
            print(json.dumps(res))

    time.sleep(25)
    print("\n=== Final balances ===")
    for label, addr, _ in (CREATOR, VALIDATOR, PUBLIC, ECOSYSTEM, HOT):
        b = walletd(["balance", "--rpc", RPC, "--address", addr])
        print(f"{label:10} {b['acp']:>20} ACP  {addr}")
    for addr in sorted(PROTECTED):
        b = walletd(["balance", "--rpc", RPC, "--address", addr])
        print(f"protected  {b['acp']:>20} ACP  {addr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
