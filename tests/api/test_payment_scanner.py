from __future__ import annotations

from uuid import uuid4

import pytest
import io
import zipfile


@pytest.fixture
def auth_headers(client):
    email = f"scanner_{uuid4().hex[:12]}@test.com"
    password = "password123"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "scanner user"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_payment_scanner_parse_acp_uri(client, auth_headers):
    res = client.post(
        "/v1/payment-scanner/parse",
        json={"raw_text": "acp:acp1qexample?amount=10", "source": "paste"},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["detected_network"] == "acp"
    assert payload["address"] == "acp1qexample"
    assert payload["amount"] == "10"
    assert payload["requires_manual_confirm"] is True


def test_payment_scanner_parse_ocr_invoice(client, auth_headers):
    addr = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"
    raw = f"""
    INVOICE #INV-2048
    Pay to: {addr}
    Total due: 12.50 USDT
    """
    res = client.post(
        "/v1/payment-scanner/parse",
        json={"raw_text": raw, "source": "ocr"},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["address"] == addr
    assert payload["amount"] == "12.5"
    assert payload["currency"] == "USDT"
    assert payload["label"] == "INV-2048"
    assert payload["confidence"] >= 0.75
    assert any("OCR" in note for note in payload["parse_notes"])


def test_payment_scanner_parse_evm_invoice(client, auth_headers):
    addr = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
    raw = f"""
    Payment request
    Send to wallet: {addr}
    Amount due: 25.00
    Network: BSC
    """
    res = client.post(
        "/v1/payment-scanner/parse",
        json={"raw_text": raw, "source": "ocr"},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["address"].lower() == addr.lower()
    assert payload["amount"] == "25"
    assert payload["detected_network"] == "bsc"


def test_payment_scanner_parse_image_uses_vision_ocr(client, auth_headers, monkeypatch):
    addr = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"

    async def _fake_extract(*, image_bytes: bytes, media_type: str) -> str:
        assert image_bytes == b"fake-image-bytes"
        assert media_type == "image/png"
        return f"INVOICE #PHOTO-1\nPay to: {addr}\nTotal due: 9.25 USDT\nNetwork: acp"

    monkeypatch.setattr(
        "app.services.payment_image_parse.extract_payment_text_from_image",
        _fake_extract,
    )
    res = client.post(
        "/v1/payment-scanner/parse-image",
        files={"file": ("receipt.png", b"fake-image-bytes", "image/png")},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["address"] == addr
    assert payload["amount"] == "9.25"
    assert payload["currency"] == "USDT"
    assert payload["requires_manual_confirm"] is True
    assert any("photo" in note.lower() for note in payload["parse_notes"])


def test_payment_scanner_parse_image_rejects_unsupported_type(client, auth_headers):
    res = client.post(
        "/v1/payment-scanner/parse-image",
        files={"file": ("notes.pdf", b"%PDF-1.4", "application/pdf")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "Unsupported image type" in res.json()["detail"]


def test_document_docx_and_acp_handoff(client, auth_headers):
    addr = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Pay to: {addr}</w:t></w:r></w:p><w:p><w:r><w:t>Total due: 12,50 ACP</w:t></w:r></w:p></w:document>')
    res = client.post("/v1/payment-scanner/parse-document", files={"file": ("invoice.docx", buffer.getvalue())}, headers=auth_headers)
    assert res.status_code == 200, res.text
    assert res.json()["amount"] == "12.5"
    assert res.json()["can_pay_acp"] is True
    assert res.json()["recommendations"]


def test_document_fiat_never_becomes_acp(client, auth_headers):
    res = client.post("/v1/payment-scanner/parse-document", files={"file": ("bill.txt", b"Total due: 25 EUR")}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["can_pay_acp"] is False


def test_document_invalid_and_unauthenticated(client, auth_headers):
    res = client.post("/v1/payment-scanner/parse-document", files={"file": ("bill.pdf", b"not a pdf")}, headers=auth_headers)
    assert res.status_code == 400
    res = client.post("/v1/payment-scanner/parse-document", files={"file": ("bill.exe", b"data")}, headers=auth_headers)
    assert res.status_code == 400
    res = client.post("/v1/payment-scanner/parse-document", files={"file": ("bill.txt", b"data")}, headers={"Authorization": ""})
    assert res.status_code in (401, 403)


def test_document_pdf_uses_document_recognition(client, auth_headers, monkeypatch):
    async def extract(**kwargs):
        assert kwargs["media_type"] == "application/pdf"
        return "Total due: 8 EUR"
    monkeypatch.setattr("app.services.payment_document_parse.extract_payment_text_from_image", extract)
    res = client.post("/v1/payment-scanner/parse-document", files={"file": ("bill.pdf", b"%PDF-1.4")}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["currency"] == "EUR"
