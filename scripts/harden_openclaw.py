"""Apply a validated least-privilege tool sandbox without printing credentials.

The gateway still runs as the user. This confines agent tools, not a compromised
gateway/plugin or a user deliberately executing code outside the sandbox.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid


def harden(config: dict, image: str) -> dict:
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
        raise ValueError("A preinstalled immutable sandbox image ID is required")
    result = copy.deepcopy(config)
    sandbox = {
        "mode": "all", "backend": "docker", "scope": "session", "workspaceAccess": "none",
        "sessionToolsVisibility": "spawned",
        "docker": {"image": image, "network": "none", "readOnlyRoot": True, "capDrop": ["ALL"],
                   "user": "65534:65534", "pidsLimit": 128, "memory": "512m", "memorySwap": "512m", "cpus": 1,
                   "tmpfs": ["/tmp", "/var/tmp", "/run"], "binds": [], "env": {}},
        "browser": {"enabled": False, "allowHostControl": False},
    }
    def protect_tools(tools: dict) -> None:
        tools["profile"] = "coding"
        tools["allow"] = ["read", "ls", "write", "edit", "apply_patch", "exec", "process"]
        tools["deny"] = sorted(set(tools.get("deny", [])) | {"gateway", "nodes", "browser", "cron", "sessions_send", "sessions_spawn"})
        tools["elevated"] = {"enabled": False}
        tools["sandbox"] = {"tools": {"allow": list(tools["allow"]), "deny": list(tools["deny"])}}
        tools.setdefault("fs", {})["workspaceOnly"] = True
        tools.setdefault("exec", {})["host"] = "sandbox"
    protect_tools(result.setdefault("tools", {}))
    agents = result.setdefault("agents", {})
    agents.setdefault("defaults", {})["sandbox"] = copy.deepcopy(sandbox)
    entries = agents.get("entries", {})
    entries = list(entries.values()) if isinstance(entries, dict) else []
    entries += agents.get("list", [])
    for entry in entries:
        entry["sandbox"] = copy.deepcopy(sandbox)
        protect_tools(entry.setdefault("tools", {}))
    return result


def private_write(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".openclaw/openclaw.json")
    parser.add_argument("--image", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    original = args.config.read_bytes()
    result = harden(json.loads(original.decode("utf-8-sig")), args.image)
    if not args.apply:
        print("Planned: all sessions sandboxed; no host workspace/network/elevated exec/browser; credentials retained outside tool containers.")
        return 0
    # Use the installed CLI, and validate against its actual schema before replacing anything.
    executable = shutil.which("openclaw.cmd" if os.name == "nt" else "openclaw")
    if not executable:
        parser.error("Installed OpenClaw CLI required for validation")
    inspect = subprocess.run(["docker", "image", "inspect", args.image], capture_output=True, timeout=30, check=False)
    if inspect.returncode != 0:
        parser.error("Sandbox image is not installed")
    candidate = args.config.with_name("security-candidate-" + uuid.uuid4().hex + ".json")
    try:
        private_write(candidate, (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        env = dict(os.environ, OPENCLAW_CONFIG_PATH=str(candidate))
        validation = subprocess.run([executable, "config", "validate"], env=env, capture_output=True, timeout=180, check=False)
        if validation.returncode != 0:
            parser.error("Installed OpenClaw schema rejected the candidate; configuration unchanged")
        if args.config.read_bytes() != original:
            parser.error("Configuration changed concurrently; retry after reviewing the change")
        backup = args.config.parent / "security-backups"
        backup.mkdir(mode=0o700, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        private_write(backup / ("before-sandbox-" + stamp + ".json"), original)
        os.replace(candidate, args.config)
        print("Validated security configuration applied; restart the gateway and verify sandbox explain before claiming containment.")
    finally:
        candidate.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
