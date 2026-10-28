"""Regressions for backlog security fixes; never execute transfers or live PSPs."""
import hashlib
import hmac
import importlib.util
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.api.routers.paid_api import _challenge_signature, PaidApiSettleRequest
from app.services import api_keys, helio_commerce


def load_script(name):
    path = Path(__file__).resolve().parents[2] / 'scripts' / name
    spec = importlib.util.spec_from_file_location('security_script_' + name.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_uses_hmac_and_rejects_legacy_prefix_hash():
    payload = b'challenge:nonce:product:1.5'
    expected = hmac.new(b'test-key', payload, hashlib.sha256).hexdigest()
    actual = _challenge_signature('test-key', 'challenge', 'nonce', 'product', '1.5')
    assert actual == expected
    assert actual != hashlib.sha256(b'test-key:' + payload).hexdigest()
    assert _challenge_signature('other-key', 'challenge', 'nonce', 'product', '1.5') != actual
    with pytest.raises(ValidationError):
        PaidApiSettleRequest(challenge_id='c', nonce='n', product_slug='p', signature='non-ascii-💣')


def test_api_key_fingerprint_is_for_generated_192_bit_tokens(monkeypatch):
    calls = []
    def generated(size):
        calls.append(size)
        return 'a' * 32
    monkeypatch.setattr(api_keys.secrets, 'token_urlsafe', generated)
    full, prefix, fingerprint = api_keys.generate_key()
    assert calls == [24]
    assert full == 'ancap_' + 'a' * 32
    assert prefix == full[:18]
    assert fingerprint == hashlib.sha256(full.encode()).hexdigest()
    assert api_keys.hash_key(full) == fingerprint


def test_helio_logs_only_static_receipt_event(caplog):
    sensitive = 'private-reference\r\nFORGED'
    with caplog.at_level(logging.INFO):
        meta = helio_commerce.summarize_helio_webhook({'event': sensitive, 'transactionObject': {'id': sensitive}})
    assert meta['transaction_id'] == sensitive
    assert caplog.records[-1].getMessage() == 'helio_webhook_received'
    assert sensitive not in caplog.text


def test_wallet_restore_uses_stdin_not_argv_or_plaintext_files(monkeypatch):
    module = load_script('restore-bridge-from-user-wallet.py')
    observed = []
    def run(command, **kwargs):
        observed.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps({'ok': True, 'result': {'address': 'fixture'}}))
    monkeypatch.setattr(module.subprocess, 'run', run)
    result = module.walletd(['address', '--keystore-file', '/dev/stdin'], keystore_json='fixture-private-key')
    assert result == {'address': 'fixture'}
    command, kwargs = observed[0]
    assert 'fixture-private-key' not in command
    assert kwargs['input'] == 'fixture-private-key'
    source = Path(module.__file__).read_text(encoding='utf-8')
    assert 'f.write(keystore_json)' not in source
    assert 'HOT_KS_PATH' not in source


def test_auth_probe_selects_only_metadata_and_excludes_raw_tokens(monkeypatch):
    module = load_script('bootstrap_ancap_docs_repo.py')
    observed = []
    def run(command, **kwargs):
        observed.append(command)
        return {'hosts': {'github.com': [{'active': True, 'login': 'fixture', 'scopes': 'repo', 'tokenSource': 'keyring', 'token': 'private-token-must-not-leak'}]}}
    monkeypatch.setattr(module, 'run_json_command', run)
    result = module.fetch_active_github_auth_context()
    assert '--jq' in observed[0]
    assert '{active, login, scopes, tokenSource}' in observed[0][-1]
    assert 'private-token-must-not-leak' not in json.dumps(result)
    assert result['login'] == 'fixture'
