"""Restricted ACP payout worker for a separate signer host.

Input: one bounded JSON object on stdin, containing an intent and optional
Ed25519 approval. Output contains a status/txid, never a key or raw signature.
Install behind a forced SSH command, with no shell/forwarding, on a separate VM.
The application/AI deploy identity must not have access to this host or policy.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

MAX_UNITS = 21_000_000_000_000_000
INTENT_FIELDS = {"request_id", "operation", "policy_hash", "key_id", "chain", "destination",
                 "amount_units", "fee_units", "expires_at"}


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def policy_hash(policy: dict) -> str:
    return hashlib.sha256(canonical(policy)).hexdigest()


def _units(value: object) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]{0,16}", value):
        raise ValueError("Amounts must be canonical integer unit strings")
    amount = int(value)
    if amount > MAX_UNITS:
        raise ValueError("Amount exceeds native ACP supply")
    return amount


def validate(intent: dict, policy: dict, approval: str | None, now: int) -> tuple[int, int]:
    if set(intent) != INTENT_FIELDS or intent["operation"] != "acp_transfer":
        raise ValueError("Unsupported signing operation or fields")
    if str(UUID(intent["request_id"])) != intent["request_id"]:
        raise ValueError("Canonical request UUID required")
    if intent["policy_hash"] != policy_hash(policy) or intent["key_id"] != policy["key_id"]:
        raise ValueError("Policy or key mismatch")
    if intent["chain"] != policy["chain"] or intent["chain"] != "acp-native":
        raise ValueError("Unsupported chain")
    if type(policy.get("chain_id")) is not int or not 0 <= policy["chain_id"] <= 0xFFFFFFFF:
        raise ValueError("A fixed native chain id is required")
    expiry = intent["expires_at"]
    if type(expiry) is not int or not now < expiry <= now + 300:
        raise ValueError("Approval lifetime must be within five minutes")
    if not isinstance(intent["destination"], str) or not re.fullmatch(r"acp1[a-z0-9]{20,100}", intent["destination"]):
        raise ValueError("Invalid destination")
    amount, fee = _units(intent["amount_units"]), _units(intent["fee_units"])
    if amount <= 0 or fee > _units(policy["max_fee_units"]):
        raise ValueError("Invalid amount or fee")
    if amount + fee > _units(policy["max_units_per_transaction"]):
        raise ValueError("Transaction limit exceeded")
    if approval:
        public = Ed25519PublicKey.from_public_bytes(base64.b64decode(policy["approval_public_key"], validate=True))
        public.verify(base64.b64decode(approval, validate=True), b"ANCAP/signing-intent/v1\0" + canonical(intent))
    elif policy.get("automatic") is not True or intent["destination"] not in policy.get("destinations", []):
        raise ValueError("Independent approval required")
    return amount, fee


def execute(intent: dict, policy: dict, approval: str | None, database: Path, walletd: Path,
            now: int | None = None) -> dict:
    now = int(time.time()) if now is None else now
    amount, fee = validate(intent, policy, approval, now)
    fingerprint = hashlib.sha256(canonical(intent)).hexdigest()
    day = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")
    database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=30, isolation_level=None)
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, day TEXT NOT NULL, units INTEGER NOT NULL, status TEXT NOT NULL, txid TEXT)")
        connection.execute("BEGIN IMMEDIATE")
        previous = connection.execute("SELECT fingerprint,status,txid FROM requests WHERE id=?", (intent["request_id"],)).fetchone()
        if previous:
            if previous[0] != fingerprint:
                raise ValueError("Request UUID reused for another intent")
            connection.execute("COMMIT")
            return {"status": previous[1], "txid": previous[2]}
        spent = connection.execute("SELECT COALESCE(SUM(units),0) FROM requests WHERE day=?", (day,)).fetchone()[0]
        if spent + amount + fee > _units(policy["max_units_per_day"]):
            raise ValueError("Daily limit exceeded")
        # All reservations, including uncertain outcomes, consume the cap. Never
        # free a reservation or retry a possibly broadcast transaction automatically.
        connection.execute("INSERT INTO requests VALUES(?,?,?,?,?,NULL)",
                           (intent["request_id"], fingerprint, day, amount + fee, "pending"))
        connection.execute("COMMIT")
        result = {"status": "unknown", "txid": None}
        try:
            completed = subprocess.run(
                [str(walletd), "--request-stdin"],
                input=json.dumps(["transfer", "--rpc", policy["rpc_url"],
                                  "--keystore-file", policy["keystore_file"], "--to", intent["destination"],
                                  "--amount-acp", _acp(amount), "--fee-acp", _acp(fee)]),
                capture_output=True, encoding="utf-8", timeout=90, check=False,
                env={"ACP_RPC_TOKEN": os.environ.get("ACP_RPC_TOKEN", ""),
                     "ACP_EXPECTED_CHAIN_ID": str(policy["chain_id"]),
                     "ACP_EXPECTED_SOURCE_ADDRESS": policy["source_address"]},
            )
            payload = json.loads(completed.stdout)
            body = payload.get("result", {})
            txid = body.get("txid")
            if completed.returncode == 0 and payload.get("ok") is True and body.get("accepted") is True and isinstance(txid, str) and re.fullmatch(r"[a-fA-F0-9]{64}", txid):
                result = {"status": "submitted", "txid": txid}
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError):
            # No helper output or underlying exception may leave this boundary.
            pass
        connection.execute("UPDATE requests SET status=?,txid=? WHERE id=?", (result["status"], result["txid"], intent["request_id"]))
        return result
    finally:
        connection.close()


def _acp(units: int) -> str:
    return f"{units // 100_000_000}.{units % 100_000_000:08d}"


def _protected_file(path: Path) -> Path:
    path = path.resolve(strict=True)
    if not path.is_file() or (os.name != "nt" and (path.stat().st_mode & 0o022 or path.stat().st_uid != 0)):
        raise ValueError("Signer configuration must not be group/world writable")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--walletd", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() == 0:
        parser.error("Run as a dedicated unprivileged user on the independent Linux signer host")
    os.umask(0o077)
    try:
        policy_path = _protected_file(args.policy)
        walletd = _protected_file(args.walletd)
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        _protected_file(Path(policy["keystore_file"]))
        if not Path(policy["keystore_file"]).is_absolute() or not args.walletd.is_absolute() or not args.database.is_absolute():
            raise ValueError("Absolute operator-controlled paths required")
        request = sys.stdin.buffer.read(16_385)
        if len(request) > 16_384:
            raise ValueError("Request too large")
        envelope = json.loads(request)
        if set(envelope) - {"intent", "approval"}:
            raise ValueError("Unknown envelope fields")
        result = execute(envelope["intent"], policy, envelope.get("approval"), args.database, walletd)
        print(json.dumps({"ok": True, **result}))
        return 0
    except Exception:
        print(json.dumps({"ok": False, "error": "Signing request denied or unavailable"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
