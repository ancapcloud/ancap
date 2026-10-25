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
    assert calls[0]["task"] == "freeform"
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
