"""rACP redeem API — fail-closed status and lookups."""
from __future__ import annotations


def test_racp_redeem_status_fail_closed(client):
    response = client.get("/v1/racp/redeem/status")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["racp_per_acp"] == 10
    assert body["token_contract"].lower().startswith("0x")
    assert body["reserve_acp_address"].startswith("acp1")
    assert "client_secret" not in body
    assert "keystore" not in str(body).lower()


def test_racp_redeem_by_tx_404(client):
    response = client.get("/v1/racp/redeem/by-tx/0x" + "ab" * 32)
    assert response.status_code == 404


def test_racp_redeem_by_id_404(client):
    response = client.get("/v1/racp/redeem/999999")
    assert response.status_code == 404


def test_racp_redeem_admin_requires_auth(client):
    response = client.get("/v1/racp/redeem/admin/open")
    assert response.status_code in {401, 403}
