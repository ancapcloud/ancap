import os
import pytest


@pytest.fixture(autouse=True)
def restore_rpc_settings_after_test():
    names = ("CHAIN_ANCHOR_DRIVER", "ACP_RPC_URL", "ETHEREUM_RPC_URL", "SOLANA_RPC_URL")
    previous = {name: os.environ.get(name) for name in names}
    yield
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    get_settings.cache_clear()

from app.config import get_settings


def _set_env(**kwargs) -> None:
    for k, v in kwargs.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)
    # Settings are cached via lru_cache
    get_settings.cache_clear()


class _StubResponse:
    def __init__(self, *, status_code: int = 200, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


class _StubAsyncClient:
    def __init__(self, *, response: _StubResponse | None = None, raise_exc: Exception | None = None):
        self._response = response
        self._raise_exc = raise_exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, timeout=None, headers=None, **kwargs):
        if self._raise_exc:
            raise self._raise_exc
        assert self._response is not None
        return self._response


def test_chain_anchor_mock_ok(client, monkeypatch):
    _set_env(CHAIN_ANCHOR_DRIVER="mock")
    r = client.post(
        "/v1/chain/anchor",
        json={"chain_id": "acp-test", "payload_type": "run", "payload_hash": "a" * 64, "payload_json": {"x": 1}},
    )
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["chain_id"] == "acp-test"
    assert j["payload_type"] == "run"
    assert j["payload_hash"] == "a" * 64
    assert j["tx_hash"].startswith("0x")


def test_chain_anchor_rpc_missing_url_503(client):
    _set_env(CHAIN_ANCHOR_DRIVER="acp", ACP_RPC_URL="")
    r = client.post(
        "/v1/chain/anchor",
        json={"chain_id": "acp-test", "payload_type": "run", "payload_hash": "b" * 64},
    )
    assert r.status_code == 503


def test_chain_anchor_rpc_success_string_result(client, monkeypatch):
    _set_env(CHAIN_ANCHOR_DRIVER="ethereum", ETHEREUM_RPC_URL="http://rpc.local")

    from app.services import chain_anchor as ca

    monkeypatch.setattr(
        ca.httpx,
        "AsyncClient",
        lambda **_kwargs: _StubAsyncClient(response=_StubResponse(json_data={"result": "0xabc123"})),
    )

    r = client.post(
        "/v1/chain/anchor",
        json={"chain_id": "ethereum", "payload_type": "run", "payload_hash": "c" * 64},
    )
    assert r.status_code == 201, r.text
    assert r.json()["tx_hash"] == "0xabc123"


def test_chain_anchor_rpc_success_object_result(client, monkeypatch):
    _set_env(CHAIN_ANCHOR_DRIVER="solana", SOLANA_RPC_URL="http://rpc.local")

    from app.services import chain_anchor as ca

    monkeypatch.setattr(
        ca.httpx,
        "AsyncClient",
        lambda **_kwargs: _StubAsyncClient(response=_StubResponse(json_data={"result": {"signature": "deadbeef"}})),
    )

    r = client.post(
        "/v1/chain/anchor",
        json={"chain_id": "solana", "payload_type": "run", "payload_hash": "d" * 64},
    )
    assert r.status_code == 201, r.text
    # service normalizes to 0x-prefixed string
    assert r.json()["tx_hash"] == "0xdeadbeef"


def test_chain_anchor_rpc_error_result_503(client, monkeypatch):
    _set_env(CHAIN_ANCHOR_DRIVER="acp", ACP_RPC_URL="http://rpc.local")

    from app.services import chain_anchor as ca

    monkeypatch.setattr(
        ca.httpx,
        "AsyncClient",
        lambda **_kwargs: _StubAsyncClient(response=_StubResponse(json_data={"error": {"message": "boom"}})),
    )

    r = client.post(
        "/v1/chain/anchor",
        json={"chain_id": "acp-test", "payload_type": "run", "payload_hash": "e" * 64},
    )
    assert r.status_code == 503

