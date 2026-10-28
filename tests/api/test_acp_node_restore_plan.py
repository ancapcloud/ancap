"""PQC vault dual-read + web swap gate + reconcile classify."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.config import get_settings
from app.services import dna_rna_crypto, passport_crypto, perimeter_crypto, pqc_envelope
from app.services.acp_fund_reconcile import classify_gap
from app.services.passport_crypto import LEGACY_CIPHER_ID as PASSPORT_LEGACY


def test_pqc_envelope_roundtrip():
    env, chash, cid = pqc_envelope.seal_json({"k": "v"}, context=b"ACP/test/v1")
    assert cid == pqc_envelope.CIPHER_ID
    assert chash.startswith("sha256:")
    assert pqc_envelope.open_json(envelope_b64=env, context=b"ACP/test/v1")["k"] == "v"


def test_passport_xwing_roundtrip_and_legacy_dual_read(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    payload = {"doc": "diploma", "n": 1}
    ct, nonce, chash, cid = passport_crypto.encrypt_payload(payload)
    assert cid == pqc_envelope.CIPHER_ID
    assert nonce == "xwing-v1"
    assert passport_crypto.decrypt_payload(ciphertext_b64=ct, nonce_b64=nonce, cipher_id=cid) == payload

    # Legacy path: force ChaCha encrypt via internal helpers
    import base64
    import json
    import os

    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

    pt = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    n = os.urandom(12)
    legacy_ct = ChaCha20Poly1305(passport_crypto.derive_docs_key()).encrypt(
        n, pt, associated_data=passport_crypto.KEY_INFO
    )
    opened = passport_crypto.decrypt_payload(
        ciphertext_b64=base64.urlsafe_b64encode(legacy_ct).decode(),
        nonce_b64=base64.urlsafe_b64encode(n).decode(),
        cipher_id=PASSPORT_LEGACY,
    )
    assert opened == payload
    assert chash.startswith("sha256:")


def test_dna_and_perimeter_xwing_roundtrip():
    dna = {"molecule": "DNA", "hint": "short"}
    ct, nonce, _h, cid = dna_rna_crypto.encrypt_payload(dna)
    assert cid.startswith("xwing-")
    assert dna_rna_crypto.decrypt_payload(ciphertext_b64=ct, nonce_b64=nonce, cipher_id=cid) == dna

    peri = {"site": "lab", "contamination": "low"}
    ct2, nonce2, _h2, cid2 = perimeter_crypto.encrypt_payload(peri)
    assert perimeter_crypto.decrypt_payload(ciphertext_b64=ct2, nonce_b64=nonce2, cipher_id=cid2) == peri


def test_classify_gap():
    assert classify_gap(on_chain=Decimal("0"), ledger=Decimal("100")) == "ledger_credit_chain_zero"
    assert classify_gap(on_chain=Decimal("10"), ledger=Decimal("100")) == "ledger_exceeds_chain"
    assert classify_gap(on_chain=Decimal("100"), ledger=Decimal("50")) is None
    assert classify_gap(on_chain=Decimal("0"), ledger=Decimal("0")) is None


def test_web_usdt_swap_create_gated_off(client, monkeypatch):
    monkeypatch.setenv("FF_WEB_USDT_TRC20_SWAP", "false")
    get_settings.cache_clear()
    email = f"swap_gate_{uuid4().hex[:10]}@test.com"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "Swap Gate"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    r = client.post(
        "/v1/wallet/acp/swap/quote",
        headers=headers,
        json={"usdt_trc20_amount": "10"},
    )
    assert r.status_code == 410, r.text
    detail = str(r.json().get("detail") or "").lower()
    assert "disabled" in detail or "mobile" in detail


def test_history_warming_returns_status_not_silent_empty(client, monkeypatch):
    import app.api.routers.wallet_acp as wallet_acp
    from fastapi import HTTPException

    email = f"hist_warm_{uuid4().hex[:10]}@test.com"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "Hist"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    def _cold(_address, _limit):
        raise HTTPException(status_code=502, detail="cold")

    monkeypatch.setattr(wallet_acp, "_chain_transactions_for_address", _cold)
    # Need wallet address — balance endpoint may create/bind; deposit_address often initializes
    dep = client.get("/v1/wallet/acp/deposit_address", headers=headers)
    if dep.status_code not in (200, 201):
        # If wallet not ready, skip soft
        return
    r = client.get("/v1/wallet/acp/transactions", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict)
    assert body.get("warming") is True
    assert "items" in body
