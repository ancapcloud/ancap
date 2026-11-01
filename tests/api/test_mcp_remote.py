"""Remote MCP Streamable HTTP + legacy SSE protocol smoke tests."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routers.mcp import router


@pytest.fixture
def mcp_client():
    # Protocol tests need no database or production background workers.
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    with TestClient(app) as client:
        yield client



def test_mcp_discovery_get(mcp_client):
    response = mcp_client.get("/v1/mcp")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "ancap-mcp"
    assert body["chatgpt"]["server_url"] == "https://ancap.cloud/api/v1/mcp"
    assert "ancap.create_payment_link" in body["tools"]
    assert response.headers.get("access-control-allow-origin") == "*"


def test_mcp_initialize_and_list_tools_unauthenticated(mcp_client):
    init = mcp_client.post(
        "/v1/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        },
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert init.status_code == 200
    init_body = init.json()
    assert init_body["result"]["serverInfo"]["name"] == "ancap-mcp"
    assert init.headers.get("mcp-session-id")

    listed = mcp_client.post(
        "/v1/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert listed.status_code == 200
    tools = listed.json()["result"]["tools"]
    names = {t["name"] for t in tools}
    assert "ancap.token_snapshot" in names
    assert "ancap.run_workflow" in names
    assert all("inputSchema" in t for t in tools)


def test_mcp_initialized_notification_returns_202(mcp_client):
    response = mcp_client.post(
        "/v1/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert response.status_code == 202


def test_mcp_paid_tool_requires_api_key(mcp_client):
    response = mcp_client.post(
        "/v1/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "ancap.create_payment_link",
                "arguments": {"title": "Test", "amount": "1"},
            },
        },
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["error"]["code"] == -32001
    assert "API key" in body["error"]["message"]


def test_mcp_legacy_unknown_session_rejected(mcp_client):
    response = mcp_client.post(
        "/v1/mcp/message?sessionId=unknown",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
    )
    assert response.status_code == 404


def test_mcp_options_cors(mcp_client):
    response = mcp_client.options("/v1/mcp")
    assert response.status_code == 204
    assert response.headers.get("access-control-allow-origin") == "*"


@pytest.mark.parametrize("payload", [[], [7], {"jsonrpc": "1.0", "id": 1, "method": "ping"}])
def test_invalid_requests_do_not_crash(mcp_client, payload):
    response = mcp_client.post("/v1/mcp", json=payload)
    assert response.status_code in (200, 400)
    assert response.json()["error"]["code"] == -32600


@pytest.mark.parametrize("params", [[], "bad", {"name": "ancap.run_workflow", "arguments": [1]}])
def test_invalid_tool_params(mcp_client, params):
    response = mcp_client.post("/v1/mcp", json={"jsonrpc":"2.0", "id":1, "method":"tools/call", "params":params})
    assert response.json()["error"]["code"] == -32602


def test_notification_never_executes_tool(mcp_client):
    response = mcp_client.post("/v1/mcp", json={"jsonrpc":"2.0", "method":"tools/call", "params":{"name":"ancap.create_claim_code", "arguments":{"amount":"10"}}})
    assert response.status_code == 202


def test_browser_origin_is_validated(mcp_client):
    assert mcp_client.get("/v1/mcp", headers={"Origin":"https://attacker.example"}).status_code == 403
    assert mcp_client.get("/v1/mcp", headers={"Origin":"https://ancap.cloud"}).status_code == 200


def test_execution_error_is_tool_result(mcp_client):
    response = mcp_client.post("/v1/mcp", json={"jsonrpc":"2.0", "id":1, "method":"tools/call", "params":{"name":"ancap.check_payment_status", "arguments":{"code":"../invoices"}}})
    assert response.json()["result"]["isError"] is True


def test_version_negotiation_and_single_batch_shape(mcp_client):
    response = mcp_client.post("/v1/mcp", json=[{"jsonrpc":"2.0", "id":1, "method":"initialize", "params":{"protocolVersion":"2025-06-18"}}])
    assert response.json()[0]["result"]["protocolVersion"] == "2025-06-18"


def test_mcp_payload_and_batch_limits(mcp_client):
    oversized = mcp_client.post('/v1/mcp', content=b' ' * 1048577, headers={'Content-Type':'application/json'})
    assert oversized.status_code == 413
    batch = mcp_client.post('/v1/mcp', json=[{'jsonrpc':'2.0','id':n,'method':'ping'} for n in range(33)])
    assert batch.status_code == 400
