"""Order-time top-up terms. Never reprice a capture/refund from the live catalog."""
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.common import Money
from app.schemas.workflow_store import CreditTopUpPricingSnapshot, WorkflowCreditPackagePublic


def _positive(money: Money) -> None:
    if not Decimal(money.amount).is_finite() or Decimal(money.amount) <= 0:
        raise ValueError("Invalid positive amount")


def build_topup_pricing_snapshot(package: WorkflowCreditPackagePublic, amount: Decimal, currency: str) -> dict:
    payment = Money(amount=str(amount), currency=currency)
    _positive(payment)
    _positive(package.credit_amount)
    return CreditTopUpPricingSnapshot(package=package.model_copy(deep=True), payment_amount=payment).model_dump(mode="json")


def package_for_topup_intent(intent) -> WorkflowCreditPackagePublic:
    payload = intent.provider_payload_json or {}
    try:
        if not isinstance(payload, dict):
            raise ValueError("Invalid pricing metadata")
        if "pricing_snapshot" in payload:
            snapshot = CreditTopUpPricingSnapshot.model_validate(payload["pricing_snapshot"])
            package = snapshot.package
            payment = snapshot.payment_amount
            if package.slug != payload.get("package_slug"):
                raise ValueError("Package identity mismatch")
        else:
            # Older real intents recorded these terms. Missing terms require
            # reconciliation, never a fallback to today's catalog.
            payment = Money.model_validate(payload["price"])
            package = WorkflowCreditPackagePublic(
                slug=payload["package_slug"], title=payload.get("package_title") or payload["package_slug"],
                description="Archived order terms", price=payment,
                credit_amount=Money.model_validate(payload["credit_amount"]),
                accepted_currencies=[payment.currency], pricing_version="legacy-recorded-terms",
            )
        _positive(payment)
        _positive(package.credit_amount)
        if payment.currency != intent.amount_currency or Decimal(payment.amount) != Decimal(intent.amount_value):
            raise ValueError("Payment terms mismatch")
        if package.credit_amount.currency != "ACP":
            raise ValueError("Unsupported credit unit")
        return package
    except (KeyError, TypeError, ValueError, InvalidOperation, ValidationError) as exc:
        raise HTTPException(status_code=409, detail="Top-up pricing evidence is invalid or missing; manual reconciliation required") from exc
