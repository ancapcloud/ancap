#!/usr/bin/env python3
"""Dependency-free stdio adapter for the hosted ANCAP MCP function catalogue."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = os.getenv("ANCAP_API_BASE", "https://ancap.cloud/api/v1").rstrip("/")
API_KEY = os.getenv("ANCAP_API_KEY", "")


def _handle_message(message):
    if not isinstance(message, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    request = urllib.request.Request(
        f"{API_BASE}/mcp", data=json.dumps(message).encode("utf-8"), headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
            return json.loads(body) if body else None
    except (urllib.error.URLError, ValueError) as exc:
        if "id" not in message:
            print(f"ANCAP MCP transport error: {exc}", file=sys.stderr)
            return None
        return {"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32000, "message": "ANCAP MCP endpoint unavailable; check ANCAP_API_BASE and connectivity."}}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            response = _handle_message(json.loads(line))
        except ValueError:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if response is not None:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
