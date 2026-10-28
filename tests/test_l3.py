"""L3: Onboarding (challenge/attest), chain anchors, stakes (basic)."""
import hashlib

from tests.conftest import unique_name


def _reasoning_solution_hash(nonce: str) -> str:
    """Client-side: first 8 hex chars of SHA256(nonce), then SHA256 of that string."""
    raw = hashlib.sha256(nonce.encode()).hexdigest()[:8]
    return hashlib.sha256(raw.encode()).hexdigest()


def _tool_use_solution_hash(nonce: str) -> str:
    """Client-side: SHA256(input) where input is nonce."""
    return hashlib.sha256(nonce.encode()).hexdigest()


def test_onboarding_challenge_and_attest(client):
    r = client.post("/v1/onboarding/challenge", json={"challenge_type": "reasoning"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["challenge_type"] == "reasoning"
    assert "nonce" in data
    assert "payload" in data
    challenge_id = data["id"]
    nonce = data["nonce"]
    solution_hash = _reasoning_solution_hash(nonce)
    r2 = client.post(
        "/v1/onboarding/attest",
        json={"challenge_id": challenge_id, "solution_hash": solution_hash},
    )
    assert r2.status_code == 201
    assert "id" in r2.json()
    assert r2.json()["challenge_id"] == challenge_id


def test_onboarding_challenge_tool_use(client):
    r = client.post("/v1/onboarding/challenge", json={"challenge_type": "tool_use"})
    assert r.status_code == 201
    data = r.json()
    assert data["challenge_type"] == "tool_use"
    assert "payload" in data
    assert data["payload"].get("task") == "echo"
    solution_hash = _tool_use_solution_hash(data["nonce"])
    r2 = client.post(
        "/v1/onboarding/attest",
        json={"challenge_id": data["id"], "solution_hash": solution_hash},
    )
    assert r2.status_code == 201


def test_onboarding_attest_invalid_solution_rejected(client):
    r = client.post("/v1/onboarding/challenge", json={"challenge_type": "reasoning"})
    assert r.status_code == 201
    challenge_id = r.json()["id"]
    r2 = client.post(
        "/v1/onboarding/attest",
        json={"challenge_id": challenge_id, "solution_hash": "a" * 64},
    )
    assert r2.status_code == 400
    assert "solution" in (r2.json().get("detail") or "").lower()


def test_chain_anchor_mock(client):
    from app.config import get_settings
    os_driver = "mock"
    # Make the driver explicit to avoid cache leakage from previous tests
    import os
    os.environ["CHAIN_ANCHOR_DRIVER"] = os_driver
    get_settings.cache_clear()
    r = client.post(
        "/v1/chain/anchor",
        json={
            "chain_id": "mock",
            "payload_type": "run_anchor",
            "payload_hash": "b" * 64,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["chain_id"] == "mock"
    assert data["payload_type"] == "run_anchor"
    assert data["payload_hash"] == "b" * 64
    assert data.get("tx_hash")
    r2 = client.get("/v1/chain/anchors", params={"limit": 5})
    assert r2.status_code == 200
    items = r2.json()
    assert isinstance(items, list)
    assert len(items) >= 1


def test_chain_anchor_driver_unknown_501(client, monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "unknown_chain")
    get_settings.cache_clear()
    try:
        r = client.post(
            "/v1/chain/anchor",
            json={"chain_id": "x", "payload_type": "run_anchor", "payload_hash": "c" * 64},
        )
        assert r.status_code == 501
        assert "not implemented" in (r.json().get("detail") or "").lower()
    finally:
        monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "mock")
        get_settings.cache_clear()


def test_chain_anchor_acp_no_rpc_url_503(client, monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "acp")
    monkeypatch.setenv("ACP_RPC_URL", "")
    get_settings.cache_clear()
    try:
        r = client.post(
            "/v1/chain/anchor",
            json={"chain_id": "acp", "payload_type": "run_anchor", "payload_hash": "d" * 64},
        )
        assert r.status_code == 503
        assert "acp" in (r.json().get("detail") or "").lower() or "configured" in (r.json().get("detail") or "").lower()
    finally:
        monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "mock")
        get_settings.cache_clear()


def test_chain_anchor_acp_success_mocked(client, monkeypatch):
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.config import get_settings
    monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "acp")
    monkeypatch.setenv("ACP_RPC_URL", "https://acp1.ancap.cloud/rpc")
    get_settings.cache_clear()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"tx_hash": "0xabcd1234"}}
    mock_post = AsyncMock(return_value=mock_response)
    try:
        with patch("app.services.chain_anchor.httpx") as m_httpx:
            m_client = AsyncMock()
            m_client.post = mock_post
            m_client.__aenter__.return_value = m_client
            m_client.__aexit__.return_value = None
            m_httpx.AsyncClient.return_value = m_client
            r = client.post(
                "/v1/chain/anchor",
                json={"chain_id": "acp", "payload_type": "stake", "payload_hash": "e" * 64},
            )
        assert r.status_code == 201
        assert r.json().get("tx_hash") == "0xabcd1234"
        assert r.json()["chain_id"] == "acp"
    finally:
        monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "mock")
        get_settings.cache_clear()


def test_chain_anchor_ethereum_no_rpc_url_503(client, monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "ethereum")
    monkeypatch.setenv("ETHEREUM_RPC_URL", "")
    get_settings.cache_clear()
    try:
        r = client.post(
            "/v1/chain/anchor",
            json={"chain_id": "ethereum", "payload_type": "run_anchor", "payload_hash": "f" * 64},
        )
        assert r.status_code == 503
        assert "ethereum" in (r.json().get("detail") or "").lower() or "configured" in (r.json().get("detail") or "").lower()
    finally:
        monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "mock")
        get_settings.cache_clear()


def test_chain_anchor_ethereum_success_mocked(client, monkeypatch):
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.config import get_settings
    monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "ethereum")
    monkeypatch.setenv("ETHEREUM_RPC_URL", "https://eth.llamarpc.com")
    get_settings.cache_clear()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"tx_hash": "0xethereum_tx_abc"}}
    mock_post = AsyncMock(return_value=mock_response)
    try:
        with patch("app.services.chain_anchor.httpx") as m_httpx:
            m_client = AsyncMock()
            m_client.post = mock_post
            m_client.__aenter__.return_value = m_client
            m_client.__aexit__.return_value = None
            m_httpx.AsyncClient.return_value = m_client
            r = client.post(
                "/v1/chain/anchor",
                json={"chain_id": "ethereum", "payload_type": "stake", "payload_hash": "g" * 64},
            )
        assert r.status_code == 201
        assert r.json().get("tx_hash") == "0xethereum_tx_abc"
        assert r.json()["chain_id"] == "ethereum"
    finally:
        monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "mock")
        get_settings.cache_clear()


def test_chain_anchor_solana_success_mocked(client, monkeypatch):
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.config import get_settings
    monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "solana")
    monkeypatch.setenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    get_settings.cache_clear()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "5VERv8MvSignatureBase58"}
    mock_post = AsyncMock(return_value=mock_response)
    try:
        with patch("app.services.chain_anchor.httpx") as m_httpx:
            m_client = AsyncMock()
            m_client.post = mock_post
            m_client.__aenter__.return_value = m_client
            m_client.__aexit__.return_value = None
            m_httpx.AsyncClient.return_value = m_client
            r = client.post(
                "/v1/chain/anchor",
                json={"chain_id": "solana", "payload_type": "run_anchor", "payload_hash": "h" * 64},
            )
        assert r.status_code == 201
        assert r.json().get("tx_hash") == "0x5VERv8MvSignatureBase58"
        assert r.json()["chain_id"] == "solana"
    finally:
        monkeypatch.setenv("CHAIN_ANCHOR_DRIVER", "mock")
        get_settings.cache_clear()


def test_stakes_require_agent(client):
    r = client.post(
        "/v1/stakes",
        json={"amount": "10", "currency": "VUSD"},
    )
    assert r.status_code == 401


def test_stake_and_list(client):
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("stake_agent"), "public_key": "k" * 32, "roles": ["buyer"]},
    )
    assert agent.status_code == 201
    agent_id = agent.json()["id"]
    client.post(
        "/v1/ledger/deposit",
        json={"account_owner_type": "agent", "account_owner_id": agent_id, "amount": {"amount": "100", "currency": "VUSD"}},
    )
    key = client.post("/v1/keys", json={"agent_id": agent_id})
    assert key.status_code == 201
    api_key = key.json()["key"]
    r = client.post(
        "/v1/stakes",
        json={"amount": "20", "currency": "VUSD"},
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "active"
    assert r.json()["amount_value"] == "20"
    r2 = client.get("/v1/stakes", params={"agent_id": agent_id})
    assert r2.status_code == 200
    assert len(r2.json()) >= 1
