"""Remote MCP tool catalogue and in-process API dispatch (Streamable HTTP / SSE)."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
from fastapi import FastAPI
from pydantic import ValidationError

from app.schemas.claim_codes import ClaimCodeCreateRequest, ClaimCodeRedeemRequest
from app.schemas.merchant import InvoiceCreateRequest, PaymentLinkCreateRequest
from app.schemas.payment_scanner import PaymentScannerParseRequest
from app.schemas.workflow_store import WorkflowRunCreateRequest

PROTOCOL_VERSION = "2025-03-26"
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}
SERVER_INFO = {"name": "ancap-mcp", "version": "0.2.0"}

# Tools that may run without an API key (public read / free preview).
PUBLIC_TOOLS = frozenset(
    {
        "ancap.check_payment_status",
    }
)

TOOL_DEFS: dict[str, dict[str, Any]] = {
    "ancap.token_snapshot": {
        "description": (
            "Run a free token snapshot workflow preview. "
            "Use this when the user wants a quick unpaid token risk glance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Token symbol or contract reference"},
                "chain": {"type": "string", "description": "Optional chain id or name"},
                "api_key": {
                    "type": "string",
                    "description": "Optional ANCAP API key (ancap_…). Prefer Authorization header when available.",
                },
            },
            "additionalProperties": True,
        },
        "path": "/workflow-store/runs",
        "method": "POST",
        "build": lambda args: {
            "workflow_slug": "token-risk-report",
            "payment_currency": "ACP",
            "unlock_full_result": False,
            "inputs": {k: v for k, v in args.items() if k != "api_key"},
        },
    },
    "ancap.create_risk_report": {
        "description": (
            "Create a paid token risk report workflow run. "
            "Requires ANCAP API key. Charges apply — confirm with the user first."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "chain": {"type": "string"},
                "api_key": {"type": "string", "description": "ANCAP API key (ancap_…)"},
            },
            "additionalProperties": True,
        },
        "path": "/workflow-store/runs",
        "method": "POST",
        "build": lambda args: {
            "workflow_slug": "token-risk-report-pro",
            "payment_currency": "ACP",
            "unlock_full_result": True,
            "inputs": {k: v for k, v in args.items() if k != "api_key"},
        },
    },
    "ancap.create_payment_link": {
        "description": (
            "Create an ANCAP Pay payment link. Requires API key. "
            "Use when the user wants to invoice or collect ACP/stable payment."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "amount": {"type": "string"},
                "currency": {"type": "string", "description": "ACP, SACP, USDT, or USD"},
                "description": {"type": "string"},
                "expires_in_hours": {"type": "integer"},
                "api_key": {"type": "string", "description": "ANCAP API key (ancap_…)"},
            },
            "required": ["title", "amount"],
            "additionalProperties": True,
        },
        "path": "/pay/payment-links",
        "method": "POST",
        "build": lambda args: {k: v for k, v in args.items() if k != "api_key"},
    },
    "ancap.create_invoice": {
        "description": "Create a merchant invoice with optional payment link. Requires API key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "ANCAP API key (ancap_…)"},
            },
            "additionalProperties": True,
        },
        "path": "/pay/invoices",
        "method": "POST",
        "build": lambda args: {k: v for k, v in args.items() if k != "api_key"},
    },
    "ancap.check_payment_status": {
        "description": "Get public payment link status by short code. No API key required.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Public payment link code"},
            },
            "required": ["code"],
        },
        "path": None,  # dynamic
        "method": "GET",
        "build": None,
    },
    "ancap.create_claim_code": {
        "description": "Lock ACP balance into a claim code. Requires API key. Confirm amount with the user first.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "string"},
                "currency": {"type": "string"},
                "max_redemptions": {"type": "integer"},
                "expires_in_hours": {"type": "integer"},
                "api_key": {"type": "string", "description": "ANCAP API key (ancap_…)"},
            },
            "required": ["amount"],
            "additionalProperties": True,
        },
        "path": "/claim-codes/create",
        "method": "POST",
        "build": lambda args: {k: v for k, v in args.items() if k != "api_key"},
    },
    "ancap.redeem_claim_code": {
        "description": "Redeem a claim code to wallet credits. Requires API key of the redeeming account.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "pin": {"type": "string"},
                "api_key": {"type": "string", "description": "ANCAP API key (ancap_…)"},
            },
            "required": ["code"],
            "additionalProperties": True,
        },
        "path": "/claim-codes/redeem",
        "method": "POST",
        "build": lambda args: {k: v for k, v in args.items() if k != "api_key"},
    },
    "ancap.quote_smart_pay": {
        "description": "Parse a payment QR / URI for manual confirmation. Requires API key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw": {"type": "string", "description": "QR payload or payment URI"},
                "api_key": {"type": "string", "description": "ANCAP API key (ancap_…)"},
            },
            "additionalProperties": True,
        },
        "path": "/payment-scanner/parse",
        "method": "POST",
        "build": lambda args: {k: v for k, v in args.items() if k != "api_key"},
    },
    "ancap.run_workflow": {
        "description": (
            "Run any workflow by slug via the workflow store. Requires API key for paid runs. "
            "Confirm charges with the user before unlock_full_result=true."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_slug": {"type": "string"},
                "payment_currency": {"type": "string"},
                "unlock_full_result": {"type": "boolean"},
                "inputs": {"type": "object"},
                "api_key": {"type": "string", "description": "ANCAP API key (ancap_…)"},
            },
            "required": ["workflow_slug"],
            "additionalProperties": True,
        },
        "path": "/workflow-store/runs",
        "method": "POST",
        "build": lambda args: {k: v for k, v in args.items() if k != "api_key"},
    },
}


# Derive function contracts from the same models used by HTTP routes.
REQUEST_MODELS = {
    "ancap.create_payment_link": PaymentLinkCreateRequest,
    "ancap.create_invoice": InvoiceCreateRequest,
    "ancap.create_claim_code": ClaimCodeCreateRequest,
    "ancap.redeem_claim_code": ClaimCodeRedeemRequest,
    "ancap.quote_smart_pay": PaymentScannerParseRequest,
    "ancap.run_workflow": WorkflowRunCreateRequest,
}
for _name, _model in REQUEST_MODELS.items():
    _schema = _model.model_json_schema()
    _schema["properties"]["api_key"] = {"type": "string", "description": "Account API key; prefer Authorization header."}
    TOOL_DEFS[_name]["inputSchema"] = _schema
TOOL_DEFS["ancap.token_snapshot"]["description"] += " Requires an account API key; preview does not unlock a paid result."
TOOL_DEFS["ancap.quote_smart_pay"]["build"] = lambda args: {
    **{k: v for k, v in args.items() if k not in {"api_key", "raw"}},
    "raw_text": args.get("raw_text", args.get("raw")),
}


def list_tools_payload() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": meta["description"],
            "inputSchema": meta["inputSchema"],
        }
        for name, meta in TOOL_DEFS.items()
    ]


def extract_api_key(header_auth: str | None, header_x_api_key: str | None, arguments: dict[str, Any]) -> str:
    if header_x_api_key and header_x_api_key.strip():
        return header_x_api_key.strip()
    if header_auth:
        token = header_auth.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        if token.startswith("ancap_"):
            return token
    raw_arg = arguments.get("api_key")
    if isinstance(raw_arg, str) and raw_arg.strip():
        return raw_arg.strip()
    return ""


async def dispatch_tool(
    *,
    app: FastAPI,
    name: str,
    arguments: dict[str, Any],
    api_key: str,
) -> dict[str, Any]:
    if name not in TOOL_DEFS:
        raise KeyError(name)
    meta = TOOL_DEFS[name]
    if name not in PUBLIC_TOOLS and not api_key:
        raise PermissionError(
            "ANCAP API key required. Create one at https://ancap.cloud/developers/connect "
            "and pass it as tool argument api_key, or send Authorization: Bearer ancap_… / X-API-Key."
        )

    if name == "ancap.check_payment_status":
        code = str(arguments.get("code") or "").strip()
        if not code:
            raise ValueError("code is required")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", code):
            raise ValueError("Invalid payment link code")
        path = f"/pay/{code}"
        method = "GET"
        payload = None
    else:
        path = meta["path"]
        method = meta["method"]
        builder = meta["build"]
        payload = builder(arguments) if builder else None
        model = REQUEST_MODELS.get(name)
        if model:
            payload = model.model_validate(payload).model_dump(mode="json")

    headers: dict[str, str] = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"

    # Nested ASGI call — avoids self-HTTP deadlock on a single uvicorn worker.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://ancap.internal") as client:
        if method == "GET":
            response = await client.get(f"/v1{path}", headers=headers, timeout=60.0)
        else:
            headers["Content-Type"] = "application/json"
            response = await client.request(
                method,
                f"/v1{path}",
                headers=headers,
                content=json.dumps(payload or {}).encode("utf-8"),
                timeout=60.0,
            )

    body_text = response.text
    try:
        body: Any = response.json() if body_text else {}
    except Exception:
        body = {"raw": body_text}

    if response.status_code >= 400:
        detail = body.get("detail") if isinstance(body, dict) else body
        raise RuntimeError(f"HTTP {response.status_code}: {detail}")
    return body if isinstance(body, dict) else {"result": body}


def jsonrpc_result(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def jsonrpc_error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


async def handle_mcp_message(
    *,
    app: FastAPI,
    message: dict[str, Any],
    header_auth: str | None,
    header_x_api_key: str | None,
) -> dict[str, Any] | None:
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return jsonrpc_error(message.get("id"), -32600, "Invalid Request")
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params", {})
    if not isinstance(params, dict):
        return jsonrpc_error(msg_id, -32602, "params must be an object")
    if "id" not in message:
        return None

    if method == "initialize":
        return jsonrpc_result(
            msg_id,
            {
                "protocolVersion": params.get("protocolVersion") if params.get("protocolVersion") in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
                "instructions": (
                    "ANCAP remote MCP. ChatGPT URL: https://ancap.cloud/api/v1/mcp "
                    "(Streamable HTTP; auth: No authentication for discover, pass api_key on paid tools "
                    "or use Authorization/X-API-Key). Create keys at https://ancap.cloud/developers/connect. "
                    "Confirm charges before paid workflow, claim, or payment tools."
                ),
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return jsonrpc_result(msg_id, {"tools": list_tools_payload()})

    if method == "ping":
        return jsonrpc_result(msg_id, {})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            return jsonrpc_error(msg_id, -32602, "arguments must be an object")
        if not isinstance(name, str) or name not in TOOL_DEFS:
            return jsonrpc_error(msg_id, -32601, f"Unknown tool: {name}")
        api_key = extract_api_key(header_auth, header_x_api_key, arguments)
        try:
            result = await dispatch_tool(app=app, name=name, arguments=arguments, api_key=api_key)
            return jsonrpc_result(
                msg_id,
                {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]},
            )
        except PermissionError as exc:
            return jsonrpc_error(msg_id, -32001, str(exc))
        except (ValueError, ValidationError) as exc:
            return jsonrpc_result(msg_id, {"isError": True, "content": [{"type": "text", "text": str(exc)}]})
        except Exception as exc:
            return jsonrpc_result(msg_id, {"isError": True, "content": [{"type": "text", "text": str(exc)}]})

    if msg_id is not None:
        return jsonrpc_error(msg_id, -32601, f"Unsupported method: {method}")
    return None
