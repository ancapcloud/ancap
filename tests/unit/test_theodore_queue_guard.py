"""Unit checks for Theodore queue/receipt guard (no DB)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.theodore_queue_guard import (
    VALID_ROP,
    parse_queue_status,
    select_open_tasks,
    validate_receipt,
)


def test_parse_queue_marks_cost03_done():
    text = Path("THEODORE_QUEUE.md").read_text(encoding="utf-8")
    status = parse_queue_status(text)
    assert status.get("COST-03") == "done"
    assert "COST-03" not in select_open_tasks(status)


def test_queue_exposes_open_rop_tasks_without_fake_ids():
    text = Path("THEODORE_QUEUE.md").read_text(encoding="utf-8")
    status = parse_queue_status(text)
    rop_tasks = {task for task in status if task.startswith("ROP-")}
    assert rop_tasks, "queue must mark ROP tasks with '## [ ] ROP-0x' headers"
    assert rop_tasks <= VALID_ROP, f"queue invented ids outside the pilot roadmap: {rop_tasks - VALID_ROP}"
    assert any(status[task] == "open" for task in rop_tasks), (
        "queue must not mark every ROP task done while ROP-01/02/03/05 acceptance stays open"
    )


def test_validate_receipt_rejects_fake_rop_and_reopen(tmp_path: Path):
    bad = tmp_path / "bad-receipt.json"
    bad.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "task_id": "ROP-06-packet-templates",
                "status": "partial",
                "checked": ["ROP-05", "ROP-06"],
                "next": "COST-03 admin GET again",
            }
        ),
        encoding="utf-8",
    )
    errors = validate_receipt(bad, {"COST-03": "done", "ROP-05": "open"})
    assert any("ROP-06" in err for err in errors)
    assert any("COST-03" in err for err in errors)


def test_two_consecutive_selections_skip_done_cost03():
    text = Path("THEODORE_QUEUE.md").read_text(encoding="utf-8")
    first = select_open_tasks(parse_queue_status(text))
    second = select_open_tasks(parse_queue_status(text))
    assert "COST-03" not in first
    assert first == second


def test_unknown_rop_ids_rejected_in_every_receipt_field(tmp_path):
    receipt = tmp_path / "receipt.json"
    for field in ("task_id", "completed_task", "next", "next_steps", "checked"):
        receipt.write_text(json.dumps({field: "rop-08-packet-templates"}))
        errors = validate_receipt(receipt, {})
        assert any("ROP-08" in error for error in errors), field
    receipt.write_text(json.dumps({"task_id": "ROP-05", "next": "ROP-04"}))
    assert validate_receipt(receipt, {}) == []


def test_forbidden_tasks_rejected_without_queue_header(tmp_path):
    receipt = tmp_path / "receipt.json"
    for field in ("task_id", "completed_task", "next", "next_steps"):
        receipt.write_text(json.dumps({field: "COST-05-attribution"}))
        errors = validate_receipt(receipt, {}, ["COST-05"])
        assert any("forbidden task COST-05" in error for error in errors), field
    receipt.write_text(json.dumps({"checked": ["COST-05"], "next": "ROP-05"}))
    assert validate_receipt(receipt, {}, ["COST-05"]) == []


def test_forbid_task_cli_checks_receipt(tmp_path):
    from scripts.theodore_queue_guard import main

    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"task_id": "ROP-05", "status": "partial", "next": "COST-05"}))
    result = main(["--receipt", str(receipt), "--forbid-task", "COST-05"])
    assert result == 1
