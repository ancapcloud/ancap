from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from app.services import stripe_payments


def settings(base="https://api.stripe.com/v1", environment="production", allow=False):
    return SimpleNamespace(stripe_api_base=base, environment=environment,
                           stripe_allow_local_test_api=allow, stripe_secret_key="stripe_test_key")


@pytest.mark.parametrize("base", [
    "http://api.stripe.com/v1", "https://api.stripe.com.evil.example/v1",
    "https://api.stripe.com@evil.example/v1", "https://api.stripe.com:444/v1",
    "https://api.stripe.com/v1?proxy=evil", "https://api.stripe.com/v1#fragment",
    "http://127.0.0.1:8080/v1", "http://169.254.169.254/v1",
])
@pytest.mark.asyncio
async def test_production_blocks_untrusted_endpoint_before_creating_client(monkeypatch, base):
    monkeypatch.setattr(stripe_payments, "get_settings", lambda: settings(base, allow=True))
    def forbidden_client(**kwargs):
        pytest.fail("Blocked endpoints must never receive a request or Authorization header")
    monkeypatch.setattr(stripe_payments.httpx, "AsyncClient", forbidden_client)
    with pytest.raises(HTTPException) as caught:
        await stripe_payments._stripe_request("POST", "/payment_intents")
    assert caught.value.status_code == 503


@pytest.mark.parametrize("base", ["http://localhost:9000/v1", "http://127.0.0.1/v1", "http://[::1]:8080/v1"])
def test_loopback_override_is_explicit_and_development_only(base):
    assert stripe_payments._stripe_request_base(settings(base, "development", True)) == base
    with pytest.raises(HTTPException):
        stripe_payments._stripe_request_base(settings(base, "development", False))
    with pytest.raises(HTTPException):
        stripe_payments._stripe_request_base(settings(base, "production", True))


@pytest.mark.parametrize("base", [
    "https://localhost.evil.example/v1", "http://localhost:99999/v1",
    "http://user:pass@localhost/v1", "http://localhost/v1?redirect=evil",
    "http://localhost/other", "http://[::1", "http://localhost/v1\\@evil.example",
])
def test_even_test_override_does_not_allow_arbitrary_hosts_or_urls(base):
    with pytest.raises(HTTPException):
        stripe_payments._stripe_request_base(settings(base, "test", True))


@pytest.mark.parametrize("response_status", [200, 302, 502])
@pytest.mark.parametrize("path", ["/customers", "/customers/cus_fixture/payment_methods", "/payment_methods/pm_fixture",
                                  "/payment_methods/pm_fixture/detach", "/payment_intents", "/payment_intents/pi_fixture"])
@pytest.mark.asyncio
async def test_official_endpoint_never_follows_redirects(monkeypatch, response_status, path):
    calls = []
    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def request(self, method, url, **kwargs):
            calls.append((method, url))
            if response_status == 502:
                return httpx.Response(502, text="not-json upstream content")
            return httpx.Response(response_status, headers={"location": "https://evil.example"}, json={"id": "pi_fixture"})
    monkeypatch.setattr(stripe_payments, "get_settings", settings)
    monkeypatch.setattr(stripe_payments.httpx, "AsyncClient", FakeClient)
    if response_status >= 300:
        with pytest.raises(HTTPException) as caught:
            await stripe_payments._stripe_request("POST", path)
        assert caught.value.status_code == 502
        assert caught.value.detail == "Stripe API request failed"
    else:
        assert await stripe_payments._stripe_request("POST", path) == {"id": "pi_fixture"}
    assert calls == [("POST", f"https://api.stripe.com/v1{path}")]


@pytest.mark.parametrize("path", ["//evil.example", "/../customers", "/customers?x=1", "/%2e%2e/customers", "/payment_methods/pm_x/customers", "/payment_intents/pm_wrong_kind"])
@pytest.mark.asyncio
async def test_endpoint_paths_cannot_escape_api_prefix(monkeypatch, path):
    monkeypatch.setattr(stripe_payments, "get_settings", settings)
    def forbidden_client(**kwargs):
        pytest.fail("Invalid paths must be rejected before creating an HTTP client")
    monkeypatch.setattr(stripe_payments.httpx, "AsyncClient", forbidden_client)
    with pytest.raises(HTTPException) as caught:
        await stripe_payments._stripe_request("GET", path)
    assert caught.value.status_code == 400
