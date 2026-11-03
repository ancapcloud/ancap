"""Validate Theodore queue/result markers before another development cycle.

This does not run the OpenClaw executor. It only checks repository inputs that
the executor is supposed to read, so a second cycle cannot honestly reopen a
task that the queue already marks complete.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "THEODORE_QUEUE.md"
ROADMAP = ROOT / "docs" / "RESEARCH_OPERATIONS_PILOT_ROADMAP.md"
VALID_ROP = {"ROP-01", "ROP-02", "ROP-03", "ROP-04", "ROP-05"}
FAKE_ROP = {"ROP-06", "ROP-07"}


def parse_queue_status(text: str) -> dict[str, str]:
    status: dict[str, str] = {}
    for match in re.finditer(r"^## \[( |x|~)\] ([A-Z]+-\d+)\b", text, re.M):
        mark, task = match.group(1), match.group(2)
        status[task] = {" ": "open", "x": "done", "~": "partial"}[mark]
    return status


def roadmap_has_fake_rop(text: str) -> list[str]:
    found: list[str] = []
    for fake in sorted(FAKE_ROP):
        if re.search(rf"^###\s+{fake}\b", text, re.M):
            found.append(fake)
    return found


def validate_receipt(
    path: Path, queue_status: dict[str, str], forbidden_tasks: list[str] | None = None
) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return errors
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return [f"receipt unreadable: {exc}"]
    if not isinstance(data, dict):
        return ["receipt must be a JSON object"]

    task_id = json.dumps([data.get("task_id"), data.get("completed_task")])
    next_step = json.dumps([data.get("next"), data.get("next_steps")])
    fields = {key: data.get(key) for key in (
        "task_id", "completed_task", "next", "next_steps", "checked"
    )}
    blob = json.dumps(fields, ensure_ascii=False).upper()
    for token in sorted(set(re.findall(r"\bROP-\d+\b", blob))):
        if token not in VALID_ROP:
            errors.append(f"receipt invents unknown roadmap id {token}")

    proposed_work = task_id + " " + next_step
    for task in forbidden_tasks or []:
        if re.search(rf"\b{re.escape(task)}\b", proposed_work, re.I):
            errors.append(f"receipt proposes forbidden task {task}")

    for task, state in queue_status.items():
        if state != "done":
            continue
        # Re-opening a done queue item as the active next step is the observed loop.
        if re.search(rf"\b{re.escape(task)}\b", next_step, re.I):
            errors.append(f"receipt next still points at completed {task}")
        if data.get("status") in {"completed", "partial"} and re.search(
            rf"\b{re.escape(task)}\b", task_id, re.I
        ):
            # Claiming a completed queue item as the current task_id is also a reopen.
            errors.append(f"receipt task_id reopens completed {task}")
    return errors


def select_open_tasks(queue_status: dict[str, str]) -> list[str]:
    return sorted(task for task, state in queue_status.items() if state == "open")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path.home() / ".openclaw" / "workspace" / "state" / "theodore-last-result.json",
        help="Optional Theodore receipt JSON to validate",
    )
    parser.add_argument(
        "--forbid-task",
        action="append",
        default=[],
        help="Task ids that must not be proposed again (repeat to add more)",
    )
    args = parser.parse_args(argv)

    queue_text = QUEUE.read_text(encoding="utf-8")
    roadmap_text = ROADMAP.read_text(encoding="utf-8")
    queue_status = parse_queue_status(queue_text)
    errors: list[str] = []

    for fake in roadmap_has_fake_rop(roadmap_text):
        errors.append(f"pilot roadmap unexpectedly defines {fake}")
    if queue_status.get("COST-03") != "done":
        errors.append("COST-03 must stay marked [x] after the canonical GET landed")
    for task in args.forbid_task:
        if queue_status.get(task) == "open":
            errors.append(f"forbidden task {task} is still open in THEODORE_QUEUE.md")

    errors.extend(validate_receipt(args.receipt, queue_status, args.forbid_task))

    # Two consecutive dry runs: a completed COST-03 must not be reselected.
    first = select_open_tasks(queue_status)
    second_status = parse_queue_status(QUEUE.read_text(encoding="utf-8"))
    second = select_open_tasks(second_status)
    if queue_status.get("COST-03") == "done" and second_status.get("COST-03") == "done":
        print("queue_guard: COST-03 remains done across two reads")
    else:
        errors.append("COST-03 changed between consecutive queue reads")
    if "COST-03" in first or "COST-03" in second:
        errors.append("COST-03 must not appear in open-task selection")

    if errors:
        for err in errors:
            print(f"queue_guard error: {err}", file=sys.stderr)
        return 1
    print("queue_guard: ok")
    print("open_tasks:", ", ".join(second) or "(none marked open with ## [ ] headers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
