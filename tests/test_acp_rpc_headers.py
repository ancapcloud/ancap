from app.services.acp_rpc import ACP_RPC_USER_AGENT, acp_rpc_headers


def test_acp_rpc_headers_include_user_agent():
    headers = acp_rpc_headers()
    assert headers["User-Agent"] == ACP_RPC_USER_AGENT
    assert headers["Content-Type"] == "application/json"


def test_acp_rpc_headers_with_valid_token(monkeypatch):
    """Test that x-acp-rpc-token header is included when token is set."""
    monkeypatch.setenv("ACP_RPC_TOKEN", "unit-test-token")
    from app.config import get_settings
    get_settings.cache_clear()
    headers = acp_rpc_headers()
    assert headers["x-acp-rpc-token"] == "unit-test-token"


def test_acp_rpc_headers_without_token(monkeypatch):
    """Test that x-acp-rpc-token header is absent when token is empty or whitespace."""
    monkeypatch.setenv("ACP_RPC_TOKEN", "")
    from app.config import get_settings
    get_settings.cache_clear()
    headers = acp_rpc_headers()
    assert "x-acp-rpc-token" not in headers or headers.get("x-acp-rpc-token") == ""


def test_acp_rpc_headers_with_whitespace_token(monkeypatch):
    """Test that x-acp-rpc-token header is absent when token is whitespace."""
    monkeypatch.setenv("ACP_RPC_TOKEN", "  ")
    from app.config import get_settings
    get_settings.cache_clear()
    headers = acp_rpc_headers()
    assert "x-acp-rpc-token" not in headers or headers.get("x-acp-rpc-token").strip() == ""


def test_acp_rpc_call_preserves_explicit_empty_params(monkeypatch):
    """An explicit {} must not be rewritten to [] (JSON-RPC named params)."""
    import asyncio
    from types import SimpleNamespace

    from app.services import acp_rpc

    sent = []

    class _Response:
        def json(self):
            return {"result": "ok"}

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json, headers):
            sent.append(json["params"])
            return _Response()

    monkeypatch.setattr(acp_rpc, "get_settings", lambda: SimpleNamespace(acp_rpc_url="http://unit.invalid"))
    monkeypatch.setattr(acp_rpc.httpx, "AsyncClient", _Client)

    for params in ({}, [], None):
        assert asyncio.run(acp_rpc.acp_rpc_call("getinfo", params)) == "ok"
    assert sent == [{}, [], []]
