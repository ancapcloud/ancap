from uuid import uuid4
import pytest
from app.config import get_settings
from app.api.routers import robinhood_listing as listing
from app.api.deps import require_platform_admin
from tests.api.test_workflow_store import _deposit_user_credits


ADDRESS = "0x" + uuid4().hex + "ab" * 4

@pytest.mark.parametrize("chain", [4663, 46630])
def test_listing_lifecycle(client, monkeypatch, chain):
    monkeypatch.setattr(get_settings(), "platform_admin_emails", "operator@example.org")
    base = "/v1/workflow-store"
    res = client.post(
        base + "/runs",
        json={
            "workflow_slug": "exchange-listing-submission-pack",
            "payment_currency": "ACP",
            "unlock_full_result": True,
            "inputs": {},
        },
    )
    assert res.status_code == 201, res.text
    run = res.json()
    path = base + "/robinhood/" + run["id"]
    assert client.get(path).json() is None
    draft = {
        "chain_id": chain,
        "address": ADDRESS,
        "website": "https://example.org",
        "description": "Token description",
        "contact": "private@example.org",
    }

    async def offline(*args):
        raise ValueError("offline")

    monkeypatch.setattr(listing, "inspect_contract", offline)
    assert client.put(path, json=draft).json()["status"] == "draft"

    async def verified(*args):
        return {"metadata": {"symbol": "RH"}, "missing": ["name", "decimals"]}

    monkeypatch.setattr(listing, "inspect_contract", verified)
    row = client.put(path, json=draft).json()
    assert row["status"] == "verified"
    version = {"version": row["version"]}
    assert client.post(path + "/submit", json=version).status_code == 402
    _deposit_user_credits(client, amount=run["price"]["amount"])
    payment = client.post(
        base + "/runs/" + run["id"] + "/payment-intents",
        json={"payment_method": "credits"},
    )
    assert payment.status_code == 201, payment.text
    assert client.post(base + "/runs/" + run["id"] + "/execute").status_code == 200
    for _ in range(2):
        assert client.post(path + "/submit", json=version).json()["status"] == "pending"
    review = base + "/robinhood/review/" + run["id"]
    payload = dict(version, decision="revision", comment="Add details")
    assert client.post(review, json=payload).status_code == 403
    client.app.dependency_overrides[require_platform_admin] = lambda: "test-operator"
    try:
        assert client.post(review, json=payload).json()["status"] == "revision"
        draft["description"] = "Revised token description"
        row = client.put(path, json=draft).json()
        assert client.post(path + "/submit", json=version).status_code == 409
        version = {"version": row["version"]}
        assert client.post(path + "/submit", json=version).json()["status"] == "pending"
        assert (
            client.post(
                review, json=dict(version, decision="approved", comment="OK")
            ).json()["status"]
            == "approved"
        )
        cards = client.get(base + "/robinhood/catalog").json()
        assert all("contact" not in c and c["chain_id"] == 4663 for c in cards)
        if chain == 4663:
            assert row["packet"] in cards
    finally:
        del client.app.dependency_overrides[require_platform_admin]


def test_standard_exchange_pack_runs_without_listing(client):
    run = client.post(
        "/v1/workflow-store/runs",
        json={
            "workflow_slug": "exchange-listing-submission-pack",
            "payment_currency": "ACP",
            "unlock_full_result": True,
            "inputs": {"project_name": "Standard listing"},
        },
    ).json()
    path = "/v1/workflow-store/runs/" + run["id"]
    _deposit_user_credits(client, amount=run["price"]["amount"])
    assert (
        client.post(
            path + "/payment-intents", json={"payment_method": "credits"}
        ).status_code
        == 201
    )
    assert client.post(path + "/execute").json()["item"]["status"] == "completed"
    assert client.get("/v1/workflow-store/robinhood/" + run["id"]).json() is None
