import json
import subprocess
from types import SimpleNamespace

import pytest

from app.services import walletd_process as transport


def test_private_channel_excludes_secrets_from_argv_environment_and_errors(monkeypatch):
    monkeypatch.setattr(transport, "walletd_command", lambda: ["trusted-walletd"])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "provider-fixture-secret")
    monkeypatch.setenv("ACP_HOT_MNEMONIC", "parent-fixture-mnemonic")
    monkeypatch.setenv("LD_PRELOAD", "hostile-loader")
    monkeypatch.setenv("HTTP_PROXY", "http://hostile-proxy")
    monkeypatch.setenv("ACP_RPC_TOKEN", "rpc-fixture-token")
    seen = []
    def run(command, **kwargs):
        seen.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps({"ok": True, "result": {"address": "fixture"}}))
    monkeypatch.setattr(transport.subprocess, "run", run)
    result = transport.run_walletd(["address", "--mnemonic", "private-fixture-words"])
    assert result == {"address": "fixture"}
    command, kwargs = seen[0]
    assert command == ["trusted-walletd", "--request-stdin"]
    assert json.loads(kwargs["input"])[2] == "private-fixture-words"
    assert kwargs["env"] == {key: value for key, value in kwargs["env"].items()
                             if key in {"SystemRoot", "WINDIR", "TEMP", "TMP", "SSL_CERT_FILE", "SSL_CERT_DIR", "ACP_RPC_TOKEN"}}
    assert kwargs["env"]["ACP_RPC_TOKEN"] == "rpc-fixture-token"
    assert "provider-fixture-secret" not in str(command)


@pytest.mark.parametrize("output,code", [("private-fixture-secret", 1), ('{"ok":false,"error":"private-fixture-secret"}', 1), ('[]', 0), ('{"ok":true,"result":[]}', 0)])
def test_walletd_errors_never_echo_untrusted_output(monkeypatch, output, code):
    monkeypatch.setattr(transport, "walletd_command", lambda: ["trusted-walletd"])
    monkeypatch.setattr(transport.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=code, stdout=output))
    with pytest.raises(transport.WalletdError) as error:
        transport.run_walletd(["new"])
    assert "private-fixture-secret" not in str(error.value)


def test_timeout_does_not_include_input(monkeypatch):
    monkeypatch.setattr(transport, "walletd_command", lambda: ["trusted-walletd"])
    def run(*a, **k):
        raise subprocess.TimeoutExpired(["private-fixture-secret"], 1, output="private-fixture-secret")
    monkeypatch.setattr(transport.subprocess, "run", run)
    with pytest.raises(transport.WalletdTimeout, match="timed out") as error:
        transport.run_walletd(["new"])
    assert "private-fixture-secret" not in str(error.value)


def test_production_refuses_path_search(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ACP_WALLETD_PATH", "walletd")
    with pytest.raises(transport.WalletdError, match="absolute"):
        transport.walletd_command()
