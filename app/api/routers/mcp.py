"""Hosted MCP endpoints for ChatGPT / remote clients (Streamable HTTP + legacy SSE)."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from app.services.mcp_remote import (
    SERVER_INFO,
    handle_mcp_message,
    list_tools_payload,
)

router = APIRouter(tags=["MCP"])

# In-memory session map for legacy HTTP+SSE transport (single-process; fine for MVP).
_SSE_SESSIONS: dict[str, dict[str, str | None]] = {}


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": (
            "Authorization, Content-Type, Accept, Mcp-Session-Id, "
            "X-API-Key, Last-Event-ID, Mcp-Protocol-Version"
        ),
        "Access-Control-Expose-Headers": "Mcp-Session-Id",
    }


def _with_cors(response: Response) -> Response:
    for key, value in _cors_headers().items():
        response.headers[key] = value
    return response


@router.options("/mcp")
@router.options("/mcp/sse")
@router.options("/mcp/message")
async def mcp_options() -> Response:
    return _with_cors(Response(status_code=204))


@router.get("/mcp")
async def mcp_get(
    request: Request,
    accept: str | None = Header(default=None, alias="Accept"),
):
    """Streamable HTTP GET: optional SSE listen, or JSON discovery for browsers."""
    accept_l = (accept or "").lower()
    if "text/event-stream" in accept_l:
        async def empty_sse():
            yield ": ancap-mcp ready\n\n"

        response = StreamingResponse(empty_sse(), media_type="text/event-stream")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return _with_cors(response)

    body = {
        "service": "ancap-mcp",
        "transport": "streamable-http",
        "protocolVersion": "2024-11-05",
        "serverInfo": SERVER_INFO,
        "chatgpt": {
            "server_url": "https://ancap.cloud/api/v1/mcp",
            "auth": "No authentication (discover tools); pass api_key on paid tools or use Authorization/X-API-Key",
            "docs": "https://ancap.cloud/mcp",
            "connect_keys": "https://ancap.cloud/developers/connect",
        },
        "legacy_sse": "https://ancap.cloud/api/v1/mcp/sse",
        "tools": [t["name"] for t in list_tools_payload()],
    }
    return _with_cors(JSONResponse(body))


@router.post("/mcp")
async def mcp_post(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """Streamable HTTP MCP endpoint — ChatGPT / Cursor remote clients POST JSON-RPC here."""
    try:
        payload = await request.json()
    except Exception:
        return _with_cors(JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status_code=400))

    messages: list[dict[str, Any]]
    if isinstance(payload, list):
        messages = [m for m in payload if isinstance(m, dict)]
    elif isinstance(payload, dict):
        messages = [payload]
    else:
        return _with_cors(JSONResponse({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}}, status_code=400))

    responses: list[dict[str, Any]] = []
    only_notifications = True
    for message in messages:
        if message.get("id") is not None:
            only_notifications = False
        result = await handle_mcp_message(
            app=request.app,
            message=message,
            header_auth=authorization,
            header_x_api_key=x_api_key,
        )
        if result is not None:
            responses.append(result)

    if only_notifications and not responses:
        return _with_cors(Response(status_code=202))

    if len(messages) == 1 and len(responses) == 1:
        body = responses[0]
    elif len(responses) == 1 and not isinstance(payload, list):
        body = responses[0]
    else:
        body = responses

    response = JSONResponse(body)
    # Stateless: optional session id for clients that expect one after initialize.
    if (
        isinstance(payload, dict)
        and payload.get("method") == "initialize"
        and isinstance(body, dict)
        and "result" in body
    ):
        response.headers["Mcp-Session-Id"] = uuid4().hex
    return _with_cors(response)


@router.delete("/mcp")
async def mcp_delete() -> Response:
    return _with_cors(Response(status_code=405))


@router.get("/mcp/sse")
async def mcp_legacy_sse(request: Request):
    """Legacy HTTP+SSE transport (MCP 2024-11-05) for older ChatGPT clients."""
    session_id = uuid4().hex
    # Clients POST JSON-RPC to this relative endpoint after the `endpoint` event.
    message_path = f"/v1/mcp/message?sessionId={session_id}"
    # When reached via nginx /api strip, clients on ancap.cloud should use /api prefix.
    forwarded_prefix = (request.headers.get("x-forwarded-prefix") or "").rstrip("/")
    if request.url.path.startswith("/v1/"):
        # Public URL through ancap.cloud/api → backend /v1
        public_message = f"/api/v1/mcp/message?sessionId={session_id}"
    else:
        public_message = f"{forwarded_prefix}{message_path}" if forwarded_prefix else message_path

    _SSE_SESSIONS[session_id] = {"message_path": public_message}

    async def event_stream():
        # Legacy clients only need the endpoint event; JSON-RPC continues on POST /mcp/message.
        # Optional short keepalives help intermediaries; then the stream ends cleanly.
        yield f"event: endpoint\ndata: {public_message}\n\n"
        for _ in range(2):
            if await request.is_disconnected():
                return
            await asyncio.sleep(0.05)
            yield ": keepalive\n\n"

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"
    return _with_cors(response)


@router.post("/mcp/message")
async def mcp_legacy_message(
    request: Request,
    sessionId: str | None = None,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """Legacy SSE companion POST endpoint."""
    if sessionId and sessionId not in _SSE_SESSIONS:
        # Accept unknown sessions for multi-worker / restart resilience.
        _SSE_SESSIONS[sessionId] = {"message_path": None}

    try:
        payload = await request.json()
    except Exception:
        return _with_cors(JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status_code=400))

    if not isinstance(payload, dict):
        return _with_cors(JSONResponse({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}}, status_code=400))

    result = await handle_mcp_message(
        app=request.app,
        message=payload,
        header_auth=authorization,
        header_x_api_key=x_api_key,
    )
    if result is None:
        return _with_cors(Response(status_code=202))
    return _with_cors(JSONResponse(result))
