"""Remote MCP Streamable HTTP + legacy SSE protocol smoke tests."""
from __future__ import annotations


def test_mcp_discovery_get(client_unauth):
    response = client_unauth.get("/v1/mcp")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "ancap-mcp"
    assert body["chatgpt"]["server_url"] == "https://ancap.cloud/api/v1/mcp"
    assert "ancap.create_payment_link" in body["tools"]
    assert response.headers.get("access-control-allow-origin") == "*"


def test_mcp_initialize_and_list_tools_unauthenticated(client_unauth):
    init = client_unauth.post(
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

    listed = client_unauth.post(
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


def test_mcp_initialized_notification_returns_202(client_unauth):
    response = client_unauth.post(
        "/v1/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert response.status_code == 202


def test_mcp_paid_tool_requires_api_key(client_unauth):
    response = client_unauth.post(
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


def test_mcp_legacy_sse_endpoint_event(client_unauth):
    with client_unauth.stream("GET", "/v1/mcp/sse") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        lines = []
        for line in response.iter_lines():
            lines.append(line)
            if any(line.startswith("data:") for line in lines) and any(
                line.startswith("event: endpoint") for line in lines
            ):
                break
        joined = "\n".join(lines)
        assert "event: endpoint" in joined
        assert "/api/v1/mcp/message?sessionId=" in joined


def test_mcp_legacy_message_initialize(client_unauth):
    response = client_unauth.post(
        "/v1/mcp/message",
        params={"sessionId": "test-session"},
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "sse-test", "version": "0"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["serverInfo"]["name"] == "ancap-mcp"


def test_mcp_options_cors(client_unauth):
    response = client_unauth.options("/v1/mcp")
    assert response.status_code == 204
    assert response.headers.get("access-control-allow-origin") == "*"
