from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.common import Money
from app.services.credit_pricing import build_topup_pricing_snapshot, package_for_topup_intent
from app.services.stripe_payments import quote_stripe_credit_package_amount
from app.services.workflow_execution import find_credit_package


def intent(payload, amount="95", currency="USD"):
    return SimpleNamespace(provider_payload_json=payload, amount_value=Decimal(amount), amount_currency=currency)


def test_snapshot_survives_catalog_mutation_and_separates_fiat_price():
    package = find_credit_package("launch-credits").model_copy(deep=True)
    package.price = Money(amount="999", currency="ACP")
    assert quote_stripe_credit_package_amount(package, "USD") == Decimal("95.00")
    snapshot = build_topup_pricing_snapshot(package, Decimal("95"), "USD")
    package.credit_amount.amount = "5000"
    archived = package_for_topup_intent(intent({"package_slug": package.slug, "pricing_snapshot": snapshot}))
    assert archived.credit_amount.amount == "100"
    assert archived.price.amount == "999"
    assert archived.fiat_price.amount == "95"


def test_legacy_uses_recorded_terms_without_live_catalog():
    archived = package_for_topup_intent(intent({"package_slug": "removed-package", "price": {"amount": "95", "currency": "USD"}, "credit_amount": {"amount": "123", "currency": "ACP"}}))
    assert archived.credit_amount.amount == "123"
    assert archived.pricing_version == "legacy-recorded-terms"


@pytest.mark.parametrize("mutation", ["missing", "amount", "currency", "identity", "version", "credit", "unit", "type"])
def test_missing_or_corrupt_evidence_never_reprices_from_catalog(mutation):
    package = find_credit_package("launch-credits")
    snapshot = build_topup_pricing_snapshot(package, Decimal("95"), "USD")
    payload = {"package_slug": package.slug, "pricing_snapshot": deepcopy(snapshot)}
    if mutation == "missing": payload = {"package_slug": package.slug}
    elif mutation == "amount": payload["pricing_snapshot"]["payment_amount"]["amount"] = "96"
    elif mutation == "currency": payload["pricing_snapshot"]["payment_amount"]["currency"] = "EUR"
    elif mutation == "identity": payload["package_slug"] = "other-package"
    elif mutation == "version": payload["pricing_snapshot"]["schema_version"] = 2
    elif mutation == "credit": payload["pricing_snapshot"]["package"]["credit_amount"]["amount"] = "0"
    elif mutation == "unit": payload["pricing_snapshot"]["package"]["credit_amount"]["currency"] = "USD"
    elif mutation == "type": payload = ["invalid"]
    with pytest.raises(HTTPException) as caught:
        package_for_topup_intent(intent(payload))
    assert caught.value.status_code == 409


def test_stripe_never_relabels_acp_as_fiat_when_explicit_price_is_absent():
    package = find_credit_package("starter-credits").model_copy(deep=True)
    package.fiat_price = None
    for currency in ("USD", "EUR"):
        with pytest.raises(HTTPException) as caught:
            quote_stripe_credit_package_amount(package, currency)
        assert caught.value.status_code == 409
    with pytest.raises(HTTPException) as caught:
        quote_stripe_credit_package_amount(package, "GBP")
    assert caught.value.status_code == 400
