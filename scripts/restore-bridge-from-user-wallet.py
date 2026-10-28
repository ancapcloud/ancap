#!/usr/bin/env python3
"""One-shot: decrypt platform user wallet and restore bridge reserve backing."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import User, UserAcpWallet
from app.services.acp_wallet import decode_wallet_secret, decrypt_wallet_secret_with_password

EMAIL = os.environ.get("OPERATOR_EMAIL", "dragon.cat.trx@gmail.com")
WALLET_PASSWORD = os.environ.get("WALLET_PASSWORD", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
BRIDGE_RESERVE = "acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz"
CUSTODIAL_HOT = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"
RPC = "http://acp-node:8545/rpc"
RESTORE_ACP = os.environ.get("RESTORE_ACP", "800999.999999")
WALLETD = os.environ.get("ACP_WALLETD_PATH", "walletd")


def walletd(args: list[str], *, keystore_json: str | None = None) -> dict:
    r = subprocess.run([WALLETD, *args], input=keystore_json, capture_output=True, text=True, timeout=180)
    out = (r.stdout or "").strip()
    payload = json.loads(out) if out else {}
    if r.returncode != 0 or not payload.get("ok"):
        raise RuntimeError(payload.get("error") or r.stderr or "walletd failed")
    return payload["result"]


async def main() -> int:
    if not WALLET_PASSWORD:
        print("WALLET_PASSWORD env is required", file=sys.stderr)
        return 1
    if not DATABASE_URL:
        print("DATABASE_URL env is required", file=sys.stderr)
        return 1

    engine = create_async_engine(DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(UserAcpWallet, User.email)
                .join(User, User.id == UserAcpWallet.user_id)
                .where(User.email.ilike(EMAIL))
            )
        ).one_or_none()
        if row is None:
            print(f"No ACP wallet for {EMAIL}", file=sys.stderr)
            return 1
        wallet, _ = row
        if wallet.address != CUSTODIAL_HOT:
            print(f"Unexpected wallet address {wallet.address}", file=sys.stderr)
            return 1

        secret = decrypt_wallet_secret_with_password(wallet, WALLET_PASSWORD)
        _, keystore_json = decode_wallet_secret(secret)
        if not keystore_json:
            print("Wallet secret has no keystore_json", file=sys.stderr)
            return 1

        derived = walletd(["address", "--keystore-file", "/dev/stdin"], keystore_json=keystore_json)["address"]
        if derived != CUSTODIAL_HOT:
            print(f"Keystore derives {derived}, expected {CUSTODIAL_HOT}", file=sys.stderr)
            return 1

        # The encrypted database remains the source of truth. Feed the decrypted
        # keystore through a private subprocess pipe; never persist a plaintext
        # copy or expose it through argv/process listings.
        hot_before = walletd(["balance", "--rpc", RPC, "--address", CUSTODIAL_HOT])
        bridge_before = walletd(["balance", "--rpc", RPC, "--address", BRIDGE_RESERVE])
        print("Hot before:", json.dumps(hot_before))
        print("Bridge before:", json.dumps(bridge_before))

        res = walletd(
            [
                "transfer",
                "--rpc",
                RPC,
                "--keystore-file",
                "/dev/stdin",
                "--to",
                BRIDGE_RESERVE,
                "--amount-acp",
                RESTORE_ACP,
            ],
            keystore_json=keystore_json,
        )
        print("Transfer:", json.dumps(res))
        if not res.get("accepted"):
            print("Transfer not accepted", file=sys.stderr)
            return 1

        time.sleep(30)
        hot_after = walletd(["balance", "--rpc", RPC, "--address", CUSTODIAL_HOT])
        bridge_after = walletd(["balance", "--rpc", RPC, "--address", BRIDGE_RESERVE])
        print("Hot after:", json.dumps(hot_after))
        print("Bridge after:", json.dumps(bridge_after))
    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
