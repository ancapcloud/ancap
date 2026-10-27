import hashlib
import json
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from app.schemas.workflow_value import AssessmentCreate
from app.services.workflow_value import summarize_estimates, workflow_result_hash


def estimate(before=None, after=None, rate=None, unit=None):
    return SimpleNamespace(baseline_minutes=before, assisted_minutes=after, hourly_rate=rate, hourly_currency=unit)


def test_result_hash_is_canonical_and_changes_with_the_delivered_result():
    assert workflow_result_hash({"a": "結果", "b": 2}) == workflow_result_hash({"b": 2, "a": "結果"})
    assert workflow_result_hash({"a": 1}) != workflow_result_hash({"a": 2})
    result = {"a": "結果", "value": 1.5}
    assert workflow_result_hash(result) == hashlib.sha256(json.dumps(result, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def test_negative_time_and_distinct_labor_units_are_preserved():
    saved, timed, valued, values = summarize_estimates([
        estimate(Decimal("30"), Decimal("90"), Decimal("20"), "USD"),
        estimate(Decimal("120"), Decimal("60"), Decimal("15"), "EUR"),
        estimate(Decimal("90"), Decimal("30"), Decimal("4"), "ACP"),
        estimate(),
    ])
    assert Decimal(saved) == 60
    assert (timed, valued) == (3, 3)
    assert {v.currency: Decimal(v.amount) for v in values} == {"USD": -20, "EUR": 15, "ACP": 4}


def test_absent_estimates_are_unknown_while_explicit_zero_is_known():
    assert summarize_estimates([estimate()]) == (None, 0, 0, [])
    saved, timed, valued, values = summarize_estimates([estimate(0, 0, 0, "USD")])
    assert Decimal(saved) == 0 and timed == valued == 1
    assert Decimal(values[0].amount) == 0


@pytest.mark.parametrize("extra", [
    {"baseline_minutes": 1}, {"assisted_minutes": 1},
    {"hourly_rate": 1}, {"hourly_currency": "USD"},
    {"hourly_rate": 1, "hourly_currency": "USD"},
    {"baseline_minutes": -1, "assisted_minutes": 0},
    {"baseline_minutes": "NaN", "assisted_minutes": 0},
    {"baseline_minutes": 0, "assisted_minutes": 0, "hourly_rate": -1, "hourly_currency": "USD"},
    {"baseline_minutes": 0, "assisted_minutes": "0.001"},
    {"owner_user_id": "untrusted"}, {"verdict": "paid"}, {"result_hash": "bad"},
])
def test_invalid_estimates_or_privilege_fields_are_rejected(extra):
    with pytest.raises(ValidationError):
        AssessmentCreate.model_validate({"result_hash": "a" * 64, "verdict": "accepted", **extra})


def test_unit_normalization_keeps_acp_assets_distinct():
    for raw, expected in [("usd", "USD"), ("wacp", "wACP"), ("sacp", "sACP"), ("ACP", "ACP")]:
        body = AssessmentCreate(result_hash="a" * 64, verdict="accepted", baseline_minutes="1", assisted_minutes="1", hourly_rate="2", hourly_currency=raw)
        assert body.hourly_currency == expected
