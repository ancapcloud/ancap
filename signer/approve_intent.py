"""Offline approval tool: use only on an independent, clean operator device.

The dedicated approval key is NOT a wallet key. Never copy it to the AI/API host.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
from pathlib import Path
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption, Encoding, PrivateFormat, PublicFormat, load_pem_private_key,
)

from signer.worker import canonical, validate, _acp, _units


def write_private(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--init-key", action="store_true")
    parser.add_argument("--intent", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    password = getpass.getpass("Dedicated approval key password: ").encode("utf-8")
    if args.init_key:
        if len(password) < 12:
            parser.error("Use a password of at least 12 bytes")
        if password != getpass.getpass("Confirm password: ").encode("utf-8"):
            parser.error("Passwords differ")
        key = Ed25519PrivateKey.generate()
        write_private(args.private_key, key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, BestAvailableEncryption(password)))
        print(base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode())
        return 0
    if not args.intent or not args.policy or not args.output:
        parser.error("--intent, --policy and --output are required")
    key = load_pem_private_key(args.private_key.read_bytes(), password=password)
    if not isinstance(key, Ed25519PrivateKey):
        parser.error("A dedicated Ed25519 approval key is required")
    intent = json.loads(args.intent.read_text(encoding="utf-8"))
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    approval = base64.b64encode(key.sign(b"ANCAP/signing-intent/v1\0" + canonical(intent))).decode()
    validate(intent, policy, approval, int(time.time()))
    print(json.dumps(intent, indent=2, ensure_ascii=True))
    print("Native ACP amount: " + _acp(_units(intent["amount_units"])) + "; native ACP fee: " + _acp(_units(intent["fee_units"])))
    print("Verify destination, native units, fee, policy hash and expiry on THIS clean device.")
    if input("Type APPROVE " + intent["request_id"] + ": ") != "APPROVE " + intent["request_id"]:
        parser.error("Approval cancelled")
    write_private(args.output, json.dumps({"intent": intent, "approval": approval}).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
