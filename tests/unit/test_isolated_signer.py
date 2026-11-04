import base64
import json
from pathlib import Path
import subprocess
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import pytest

from signer import worker


@pytest.fixture
def setup_signer():
    key = Ed25519PrivateKey.generate()
    policy = {"key_id": "fixture", "chain": "acp-native", "chain_id": 1001, "source_address": "acp1" + "d" * 35,
              "approval_public_key": base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode(),
              "automatic": False, "destinations": [], "max_units_per_transaction": "1000", "max_units_per_day": "1500",
              "max_fee_units": "10", "rpc_url": "http://127.0.0.1:8545/rpc", "keystore_file": "/private/fixture.json"}
    def request(amount="1000", request_id=None):
        intent = {"request_id": request_id or str(uuid4()), "operation": "acp_transfer", "policy_hash": worker.policy_hash(policy),
                  "key_id": "fixture", "chain": "acp-native", "destination": "acp1" + "a" * 35,
                  "amount_units": amount, "fee_units": "0", "expires_at": 1100}
        approval = base64.b64encode(key.sign(b"ANCAP/signing-intent/v1\0" + worker.canonical(intent))).decode()
        return intent, approval
    return policy, request


def test_denies_missing_approval_tampering_expiry_raw_signing_and_limits(setup_signer):
    policy, request = setup_signer
    intent, approval = request()
    assert worker.validate(intent, policy, approval, 1000) == (1000, 0)
    with pytest.raises(ValueError, match="approval"):
        worker.validate(intent, policy, None, 1000)
    for field, value in [("destination", "acp1" + "b" * 35), ("amount_units", "999")]:
        altered = {**intent, field: value}
        with pytest.raises(InvalidSignature):
            worker.validate(altered, policy, approval, 1000)
    for altered in ({**intent, "operation": "eth_sign"}, {**intent, "expires_at": 999},
                    {**intent, "amount_units": "1001"}, {**intent, "amount_units": "1e3"},
                    {**intent, "raw_tx": "arbitrary"}, {**intent, "fee_units": "11"}):
        with pytest.raises(ValueError):
            worker.validate(altered, policy, approval, 1000)
    changed_policy = {**policy, "max_units_per_day": "100000"}
    with pytest.raises(ValueError, match="Policy"):
        worker.validate(intent, changed_policy, approval, 1000)


def test_durable_replay_and_daily_budget_include_uncertain_outcomes(setup_signer, tmp_path, monkeypatch):
    policy, request = setup_signer
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        raise subprocess.TimeoutExpired(command, 90)
    monkeypatch.setattr(worker.subprocess, "run", run)
    database = tmp_path / "private" / "signer.sqlite3"
    intent, approval = request()
    first = worker.execute(intent, policy, approval, database, Path("/trusted/walletd"), now=1000)
    replay = worker.execute(intent, policy, approval, database, Path("/trusted/walletd"), now=1000)
    assert first == replay == {"status": "unknown", "txid": None}
    assert len(calls) == 1
    second, signature = request()
    with pytest.raises(ValueError, match="Daily"):
        worker.execute(second, policy, signature, database, Path("/trusted/walletd"), now=1000)
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == [str(Path("/trusted/walletd")), "--request-stdin"]
    assert kwargs["env"]["ACP_EXPECTED_CHAIN_ID"] == "1001"
    assert "--keystore-file" in json.loads(kwargs["input"])


def test_concurrent_requests_cannot_exceed_daily_budget(setup_signer, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    policy, request = setup_signer
    calls = []
    def run(command, **kwargs):
        from types import SimpleNamespace
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps({"ok": True, "result": {"accepted": True, "txid": "a" * 64}}))
    monkeypatch.setattr(worker.subprocess, "run", run)
    database = tmp_path / "signer.sqlite3"
    def send(pair):
        try:
            return worker.execute(pair[0], policy, pair[1], database, Path("/trusted/walletd"), now=1000)["status"]
        except ValueError:
            return "denied"
    first, second = request(), request()
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(send, [first, second]))
    assert sorted(outcomes) == ["denied", "submitted"]
    assert len(calls) == 1
    chosen = first if outcomes[0] == "submitted" else second
    changed, signature = request("500", request_id=chosen[0]["request_id"])
    with pytest.raises(ValueError, match="UUID"):
        worker.execute(changed, policy, signature, database, Path("/trusted/walletd"), now=1000)


def test_automatic_mode_requires_explicit_allowlist_and_limits(setup_signer):
    policy, request = setup_signer
    intent, _ = request()
    policy.update(automatic=True, destinations=[intent["destination"]])
    intent["policy_hash"] = worker.policy_hash(policy)
    assert worker.validate(intent, policy, None, 1000) == (1000, 0)
    with pytest.raises(ValueError, match="approval"):
        worker.validate({**intent, "destination": "acp1" + "c" * 35}, policy, None, 1000)
    policy["max_units_per_transaction"] = "0"
    intent["policy_hash"] = worker.policy_hash(policy)
    with pytest.raises(ValueError, match="limit"):
        worker.validate(intent, policy, None, 1000)
