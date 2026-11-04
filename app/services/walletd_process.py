"""Private walletd transport. Never put signing material in argv or diagnostics."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess


class WalletdError(RuntimeError):
    pass


class WalletdTimeout(WalletdError):
    pass


def walletd_command() -> list[str]:
    configured = os.environ.get("ACP_WALLETD_PATH", "").strip()
    production = os.environ.get("ENVIRONMENT", "").lower() == "production"
    if production:
        configured = configured or "/usr/local/bin/walletd"
        if not Path(configured).is_absolute():
            raise WalletdError("Production walletd requires an absolute executable path")
    else:
        configured = configured or shutil.which("walletd") or ""
    if not configured or not Path(configured).is_file():
        raise WalletdError("ACP wallet helper is not configured")
    path = Path(configured).resolve()
    if production and os.name != "nt":
        stat = path.stat()
        if stat.st_uid != 0 or stat.st_mode & 0o022:
            raise WalletdError("Production walletd must be root-owned and not group/world writable")
    return [str(path)]


def run_walletd(args: list[str], timeout_s: int = 90) -> dict:
    # An explicit allowlist excludes inherited provider/SSH/GitHub/treasury secrets,
    # dynamic-loader hooks and proxy environment variables from this child.
    env = {key: os.environ[key] for key in (
        "SystemRoot", "WINDIR", "TEMP", "TMP", "SSL_CERT_FILE", "SSL_CERT_DIR", "ACP_RPC_TOKEN"
    ) if key in os.environ}
    try:
        result = subprocess.run(
            walletd_command() + ["--request-stdin"],
            input=json.dumps(args, ensure_ascii=True),
            env=env, check=False, capture_output=True, encoding="utf-8", timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise WalletdTimeout("ACP wallet helper timed out") from None
    except OSError:
        raise WalletdError("ACP wallet helper could not start") from None
    try:
        payload = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise WalletdError("ACP wallet helper returned invalid output") from None
    if not isinstance(payload, dict) or result.returncode != 0 or payload.get("ok") is not True:
        # stderr/error/stdout can contain a mnemonic, keystore or node response.
        raise WalletdError("ACP wallet helper rejected the request")
    if not isinstance(payload.get("result"), dict):
        raise WalletdError("ACP wallet helper returned invalid output")
    return payload["result"]
