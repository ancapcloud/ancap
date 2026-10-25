import io
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.services import payment_image_parse, payment_wevisone


def settings(**overrides):
    return SimpleNamespace(**({
        "smart_pay_vision_provider": "wevisone",
        "smart_pay_wevisone_url": "https://private-inference.example",
        "smart_pay_wevisone_api_key": "a" * 32,
        "mobile_smart_pay_max_image_bytes": 5_242_880,
    } | overrides))


def configure(monkeypatch, handler, **overrides):
    config = settings(**overrides)
    monkeypatch.setattr(payment_wevisone, "get_settings", lambda: config)
    monkeypatch.setattr(payment_image_parse, "get_settings", lambda: config)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(payment_wevisone.httpx, "AsyncClient",
                        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))


@pytest.mark.asyncio
async def test_photo_uses_private_worker_and_existing_parser(monkeypatch):
    address = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"

    def handler(request):
        assert str(request.url) == "https://private-inference.example/v1/payment-ocr"
        assert request.headers["authorization"] == "Bearer " + "a" * 32
        assert request.content == b"photo"
        return httpx.Response(200, json={"text": f"Pay to: {address}\nTotal due: 12.50 USDT"})

    configure(monkeypatch, handler)
    parsed = await payment_image_parse.parse_payment_image(image_bytes=b"photo", content_type="image/png")
    assert parsed.address == address
    assert parsed.amount == "12.5"
    assert parsed.currency == "USDT"
    assert parsed.confidence <= 0.82


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [
    httpx.Response(302, headers={"location": "https://elsewhere.example"}),
    httpx.Response(503), httpx.Response(200, content=b"not json"),
    httpx.Response(200, json={"text": 5}), httpx.Response(200, json=[]),
    httpx.Response(200, json={"text": "x" * 32001}),
    httpx.Response(200, content=b"x" * 65537),
])
async def test_worker_failures_never_fall_back(monkeypatch, response):
    configure(monkeypatch, lambda request: response)
    with pytest.raises(RuntimeError):
        await payment_image_parse.extract_payment_text_from_image(image_bytes=b"x", media_type="image/png")


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["", "http://worker.example", "https://user:pass@host", "https://host?x=1"])
async def test_bad_endpoint_is_rejected_before_network(monkeypatch, url):
    def forbidden(request):
        pytest.fail("Invalid endpoint must not receive a document")
    configure(monkeypatch, forbidden, smart_pay_wevisone_url=url)
    with pytest.raises(RuntimeError):
        await payment_wevisone.extract_wevisone_payment_text(image_bytes=b"x", media_type="image/png")


@pytest.mark.asyncio
async def test_pdf_is_explicitly_rejected(monkeypatch):
    configure(monkeypatch, lambda request: pytest.fail("PDF must not reach worker"))
    with pytest.raises(ValueError, match="photos only"):
        await payment_image_parse.extract_payment_text_from_image(image_bytes=b"%PDF", media_type="application/pdf")


@pytest.mark.asyncio
async def test_existing_anthropic_provider_is_preserved(monkeypatch):
    def handler(request):
        assert str(request.url) == "https://anthropic.example/v1/messages"
        assert request.headers["x-api-key"] == "test-only"
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Total due: 5 ACP"}]})
    configure(monkeypatch, handler, smart_pay_vision_provider="anthropic",
              anthropic_api_key="test-only", anthropic_base_url="https://anthropic.example",
              llm_model="test-model", llm_max_tokens=1200)
    assert await payment_image_parse.extract_payment_text_from_image(image_bytes=b"x", media_type="image/png") == "Total due: 5 ACP"


@pytest.mark.asyncio
async def test_missing_key_size_limit_and_timeout(monkeypatch):
    configure(monkeypatch, lambda request: pytest.fail("No network without configuration"),
              smart_pay_wevisone_api_key="")
    with pytest.raises(RuntimeError, match="not configured"):
        await payment_wevisone.extract_wevisone_payment_text(image_bytes=b"x", media_type="image/png")
    with pytest.raises(ValueError, match="size"):
        await payment_wevisone.extract_wevisone_payment_text(image_bytes=b"", media_type="image/png")
    monkeypatch.undo()
    def timeout(request):
        raise httpx.ReadTimeout("test timeout")
    configure(monkeypatch, timeout)
    with pytest.raises(RuntimeError, match="request failed"):
        await payment_image_parse.parse_payment_image(image_bytes=b"x", content_type="image/png")


@pytest.mark.asyncio
async def test_empty_output_and_ambiguous_amounts(monkeypatch):
    configure(monkeypatch, lambda request: httpx.Response(200, json={"text": "EMPTY"}))
    with pytest.raises(ValueError, match="No payment details"):
        await payment_image_parse.parse_payment_image(image_bytes=b"x", content_type="image/png")
    # Reconfigure only the transport response, avoiding nested client mocks.
    monkeypatch.undo()
    configure(monkeypatch, lambda request: httpx.Response(200, json={"text": "Total due: 10 USDT\nTotal due: 20 USDT"}))
    parsed = await payment_image_parse.parse_payment_image(image_bytes=b"x", content_type="image/png")
    assert parsed.amount is None
    assert parsed.confidence <= 0.45


def test_worker_auth_limits_and_sdk_contract(monkeypatch):
    Image = pytest.importorskip("PIL.Image", reason="optional inference-worker dependency")
    from scripts import wevisone_payment_worker as worker

    calls = []

    class Model:
        def predict(self, image, **kwargs):
            calls.append(kwargs)
            assert image.mode == "RGB"
            return SimpleNamespace(response="Total due: 5 USDT")

    worker.app.state.token = "a" * 32
    worker.app.state.model = Model()
    client = TestClient(worker.app)  # Deliberately no lifespan / weights in unit test.
    headers = {"authorization": "Bearer " + "a" * 32, "content-type": "image/png"}
    assert client.post("/v1/payment-ocr", content=b"x").status_code == 401
    assert client.post("/v1/payment-ocr", headers=headers, content=b"bad image").status_code == 422
    assert client.post("/v1/payment-ocr", headers=headers, content=b"").status_code == 422
    buf = io.BytesIO()
    Image.new("RGB", (2, 2)).save(buf, format="PNG")
    assert client.post("/v1/payment-ocr", headers=headers, content=buf.getvalue()).json() == {"text": "Total due: 5 USDT"}
    assert calls[0]["task"] == "ocr"
    assert calls[0]["decode_matting"] is False
    monkeypatch.setattr(worker, "MAX_BYTES", 2)
    assert client.post("/v1/payment-ocr", headers=headers, content=b"abc").status_code == 413
    monkeypatch.setattr(worker, "MAX_BYTES", 1000)
    monkeypatch.setattr(worker, "MAX_PIXELS", 1)
    assert client.post("/v1/payment-ocr", headers=headers, content=buf.getvalue()).status_code == 422
    assert len(calls) == 1
    assert worker._lock.acquire(blocking=False)
    try:
        assert client.post("/v1/payment-ocr", headers=headers, content=b"x").status_code == 503
    finally:
        worker._lock.release()


@pytest.mark.asyncio
@pytest.mark.parametrize("environment,enabled,accepted", [
    ("development", True, True), ("development", False, False),
    ("production", True, False), ("production", False, False),
])
async def test_compose_http_is_explicit_and_development_only(monkeypatch, environment, enabled, accepted):
    configure(monkeypatch, lambda request: httpx.Response(200, json={"text": "Total due: 5 ACP"}),
              environment=environment, smart_pay_wevisone_allow_local_http=enabled,
              smart_pay_wevisone_url="http://wevisone:8097")
    if accepted:
        assert await payment_wevisone.extract_wevisone_payment_text(image_bytes=b"x", media_type="image/png") == "Total due: 5 ACP"
    else:
        with pytest.raises(RuntimeError, match="HTTPS"):
            await payment_wevisone.extract_wevisone_payment_text(image_bytes=b"x", media_type="image/png")


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["http://wevisone:80", "http://other:8097", "http://wevisone:8097?x=1"])
async def test_local_http_exception_does_not_allow_other_destinations(monkeypatch, url):
    configure(monkeypatch, lambda request: pytest.fail("Must reject before sending"),
              environment="development", smart_pay_wevisone_allow_local_http=True,
              smart_pay_wevisone_url=url)
    with pytest.raises(RuntimeError):
        await payment_wevisone.extract_wevisone_payment_text(image_bytes=b"x", media_type="image/png")


@pytest.mark.asyncio
async def test_real_model_ref_markup_is_not_a_payment_uri(monkeypatch):
    address = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"
    text = f"<ref>Invoice #LOCAL-1</ref>\n<ref>Pay to: {address}</ref>\n<ref>Total due: 12.50 ACP</ref>"
    configure(monkeypatch, lambda request: httpx.Response(200, json={"text": text}))
    parsed = await payment_image_parse.parse_payment_image(image_bytes=b"x", content_type="image/png")
    assert parsed.address == address
    assert parsed.detected_network == "acp"
    assert parsed.amount == "12.5"


def test_native_ocr_spans_are_plain_text():
    Image = pytest.importorskip("PIL.Image")
    from scripts import wevisone_payment_worker as worker
    class Model:
        def predict(self, image, **kwargs):
            assert kwargs["task"] == "ocr"
            assert "prompt" not in kwargs
            return SimpleNamespace(response="<ref>Total due:</ref><box><1><2><3><4></box>, <ref>5 ACP</ref><box><4><5><6><7></box>")
    buf = io.BytesIO()
    Image.new("RGB", (2, 2)).save(buf, format="PNG")
    assert worker.recognize(buf.getvalue(), Model()) == "Total due: 5 ACP"


def test_traditional_chinese_total_and_non_uri_slashes():
    from app.services.payment_text_parse import parse_payment_text
    address = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"
    result = parse_payment_text(f"發票 / LOCAL-1 收款地址: {address} 應付總額: 12.50 ACP 網路: acp", source="ocr")
    assert result.address == address
    assert result.amount == "12.5"
    assert result.currency == "ACP"
    assert result.detected_network == "acp"


@pytest.mark.parametrize("text,amount", [("До сплати: 12.50 ACP", "12.5"), ("應付總額: 12.50 ACP", "12.5"), ("12.50 ACP / 15 EUR", None)])
def test_explicit_asset_amount_is_language_independent_and_ambiguity_safe(text, amount):
    from app.services.payment_text_parse import parse_payment_text
    result = parse_payment_text(text, source="ocr")
    assert result.amount == amount


@pytest.mark.asyncio
async def test_ocr_checksum_error_cannot_prepare_payment(monkeypatch):
    address = "acp1qzfdkqxfgyw9ysk99qsd79yxdffe338yd85vrqn9"
    configure(monkeypatch, lambda request: httpx.Response(200, json={"text": f"Pay to: {address} Total due: 12.50 ACP"}))
    parsed = await payment_image_parse.parse_payment_image(image_bytes=b"x", content_type="image/png")
    assert parsed.address is None
    assert parsed.confidence <= 0.45
    assert any("checksum failed" in note for note in parsed.parse_notes)


def test_long_whitespace_in_untrusted_ocr_does_not_stall_parser():
    from app.services.payment_text_parse import parse_payment_text
    result = parse_payment_text("сума" + " " * 32000 + "not an amount", source="ocr")
    assert result.amount is None


def test_long_digit_sequence_cannot_become_a_truncated_amount():
    from app.services.payment_text_parse import parse_payment_text
    result = parse_payment_text("0" * 32000 + " ACP", source="ocr")
    assert result.amount is None


@pytest.mark.asyncio
async def test_invalid_private_ca_fails_before_document_upload(monkeypatch, tmp_path):
    ca = tmp_path / "invalid-ca.pem"
    ca.write_text("not a certificate")
    configure(monkeypatch, lambda request: pytest.fail("Never send documents with invalid TLS trust"),
              smart_pay_wevisone_ca_file=str(ca))
    import ssl
    with pytest.raises(ssl.SSLError):
        await payment_wevisone.extract_wevisone_payment_text(image_bytes=b"x", media_type="image/png")
