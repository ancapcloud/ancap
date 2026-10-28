from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.workflow_costs import COST_CATEGORIES, CostEvidenceCreate, ReconciledCostAllocation
from app.services.workflow_costs import reconcile_run_costs


def allocation(run, line="invoice:1", **overrides):
    return ReconciledCostAllocation(workflow_run_id=run, **{
        "category": "model", "evidence_line_id": line, "evidence_amount": "10",
        "allocated_amount": "2", "currency": "USD", **overrides})


def test_unknown_is_not_zero_and_currencies_are_separate():
    run, empty = uuid4(), uuid4()
    result, unknown = reconcile_run_costs([run, empty], [allocation(run), allocation(run, "fee", category="payment_fee", currency="ACP")])
    assert result.totals_by_currency == {"USD": Decimal(2), "ACP": Decimal(2)}
    assert not result.coverage_complete
    assert unknown.totals_by_currency == {}
    assert unknown.missing_categories == list(COST_CATEGORIES)


def test_duplicate_retry_evidence_and_cross_run_overallocation_are_rejected():
    first, second = uuid4(), uuid4()
    with pytest.raises(ValueError, match="Duplicate"):
        reconcile_run_costs([first], [allocation(first), allocation(first)])
    with pytest.raises(ValueError, match="over-allocated"):
        reconcile_run_costs([first], [allocation(first, allocated_amount="6"), allocation(second, allocated_amount="5")])
    assert reconcile_run_costs([first], [allocation(first), allocation(first, "retry:2")])[0].totals_by_currency["USD"] == 4


@pytest.mark.parametrize("change", [{"currency": "EUR"}, {"category": "data"}, {"evidence_amount": "11"}])
def test_conflicting_source_evidence_is_rejected(change):
    first, second = uuid4(), uuid4()
    with pytest.raises(ValueError, match="Conflicting"):
        reconcile_run_costs([first], [allocation(first), allocation(second, **change)])


def test_explicit_zero_evidence_and_creator_payout_count_once():
    run = uuid4()
    items = [allocation(run, c, category=c, allocated_amount="0") for c in COST_CATEGORIES]
    items[-1] = allocation(run, "creator_payout", category="creator_payout", allocated_amount="3")
    result = reconcile_run_costs([run, run], items)
    assert len(result) == 1 and result[0].coverage_complete
    assert result[0].totals_by_currency == {"USD": Decimal(3)}


def test_large_precise_amounts_are_not_rounded():
    run = uuid4()
    amount = "999999999999999999.999999999999999999"
    result = reconcile_run_costs([run], [allocation(run, str(i), evidence_amount=amount, allocated_amount=amount) for i in range(2)])
    assert result[0].totals_by_currency["USD"] == Decimal("1999999999999999999.999999999999999998")


@pytest.mark.parametrize("change", [{"allocated_amount": "-1"}, {"evidence_amount": "NaN"}, {"allocated_amount": "Infinity"}, {"currency": "usd"}, {"evidence_line_id": " "}, {"estimated": True}])
def test_invalid_or_estimated_input_rejected(change):
    with pytest.raises(ValidationError):
        allocation(uuid4(), **change)


def test_evidence_batch_validates_full_distribution_at_database_precision():
    body = dict(source="provider", document_id="invoice-1", line_id="1", document_sha256="b" * 64,
        category="model", currency="USD", amount="999999999999999999.999999999999999999",
        review_note="Reviewed source document", allocations=[
            dict(workflow_run_id=uuid4(), allocated_amount="999999999999999999.999999999999999998"),
            dict(workflow_run_id=uuid4(), allocated_amount="0.000000000000000001")])
    assert len(CostEvidenceCreate(**body).allocations) == 2
    with pytest.raises(ValidationError, match="over-allocated"):
        CostEvidenceCreate(**{**body, "amount": "999999999999999999.999999999999999998"})
    with pytest.raises(ValidationError, match="Duplicate"):
        CostEvidenceCreate(**{**body, "allocations": [body["allocations"][0]] * 2})
    for change in ({"allocations": []}, {"document_sha256": "invalid"}, {"recorded_by_user_id": uuid4()}):
        with pytest.raises(ValidationError):
            CostEvidenceCreate(**{**body, **change})
