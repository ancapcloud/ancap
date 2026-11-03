"""Unit checks for Theodore queue/receipt guard (no DB)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.theodore_queue_guard import (
    parse_queue_status,
    select_open_tasks,
    validate_receipt,
)


def test_parse_queue_marks_cost03_done():
    text = Path("THEODORE_QUEUE.md").read_text(encoding="utf-8")
    status = parse_queue_status(text)
    assert status.get("COST-03") == "done"
    assert "COST-03" not in select_open_tasks(status)


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
