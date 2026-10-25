"""ACP privacy helpers: unlinkable subaddresses + UI redaction.

Matches ACP-crypto `privacy.rs` (HKDF-SHA256 + SHA256 hash20 + bech32).
Not a mixer — only address unlinkability and response minimization.
"""
from __future__ import annotations

import hashlib
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
SUBADDR_INFO_PREFIX = b"ACP/subaddr/v1/"
PRIVACY_PROFILE = "unlinkable-subaddr-v1"
DEFAULT_SUBADDR_SCAN_WINDOW = 64


def _polymod(values: list[int]) -> int:
    gen = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            chk ^= gen[i] if ((b >> i) & 1) else 0
    return chk


def _hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _convertbits(data: bytes, from_bits: int, to_bits: int, pad: bool = True) -> list[int] | None:
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << to_bits) - 1
    for value in data:
        if value < 0 or (value >> from_bits):
            return None
        acc = (acc << from_bits) | value
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & maxv)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & maxv):
        return None
    return ret


def bech32_encode(hrp: str, data: list[int]) -> str:
    values = _hrp_expand(hrp) + data
    polymod = _polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(CHARSET[d] for d in data + checksum)


def encode_acp_address(hash20: bytes) -> str:
    if len(hash20) != 20:
        raise ValueError("hash20 must be 20 bytes")
    payload = bytes([0]) + hash20
    data = _convertbits(payload, 8, 5)
    if data is None:
        raise ValueError("bech32 convertbits failed")
    return bech32_encode("acp", data)


def hkdf_32(ikm: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(ikm)


def subaddress_hash20(view_pubkey_wire: bytes, index: int) -> bytes:
    if index < 0:
        raise ValueError("index must be >= 0")
    if index > DEFAULT_SUBADDR_SCAN_WINDOW:
        raise ValueError("index exceeds DEFAULT_SUBADDR_SCAN_WINDOW")
    if index == 0:
        return hashlib.sha256(view_pubkey_wire).digest()[:20]
    info = SUBADDR_INFO_PREFIX + int(index).to_bytes(4, "little")
    material = hkdf_32(view_pubkey_wire, info)
    return hashlib.sha256(material).digest()[:20]


def subaddress_bech32(view_pubkey_wire: bytes, index: int) -> str:
    return encode_acp_address(subaddress_hash20(view_pubkey_wire, index))


def redact_address(addr: str) -> str:
    s = (addr or "").strip()
    if len(s) <= 16:
        return "acp1…"
    return f"{s[:8]}…{s[-6:]}"


def redact_tx_public(details: dict[str, Any]) -> dict[str, Any]:
    """Minimize counterparty leakage for wallet/history responses."""
    out = {
        "txid": details.get("txid"),
        "direction": details.get("direction"),
        "status": details.get("status"),
        "privacy": True,
        "privacy_profile": PRIVACY_PROFILE,
        "net_acp": details.get("net_acp") or details.get("acp"),
        "fee_acp": details.get("fee_acp"),
        "confirmations": details.get("confirmations"),
        "counterparties_redacted": True,
    }
    return out


def explorer_tx_redacted(decoded: Any) -> dict[str, Any]:
    """Public explorer summary — no full address/amount dump by default."""
    tx_count_in = 0
    tx_count_out = 0
    if isinstance(decoded, dict):
        tx_count_in = len(decoded.get("vin") or decoded.get("inputs") or [])
        tx_count_out = len(decoded.get("vout") or decoded.get("outputs") or [])
    return {
        "view": "redacted",
        "privacy_profile": PRIVACY_PROFILE,
        "input_count": tx_count_in,
        "output_count": tx_count_out,
        "note": "Full wire remains on-node; amounts/addresses hidden by default for user privacy.",
    }


def valid_acp_address_checksum(address: str) -> bool:
    """Check native ACP Bech32 without guessing or correcting OCR characters."""
    if not address.startswith("acp1") or address != address.lower() or len(address) < 11:
        return False
    try:
        values = [CHARSET.index(char) for char in address[4:]]
    except ValueError:
        return False
    return _polymod(_hrp_expand("acp") + values) == 1
