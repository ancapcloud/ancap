"""Fail closed until the same commit's applicable push CI has succeeded."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

import yaml

BLOCKING = {"Backend CI", "Frontend CI", "Crypto CI", "CodeQL", "Secret Hygiene", "Docs CI"}
WORKFLOWS = {
    "Backend CI": "backend-ci.yml", "Frontend CI": "frontend-ci.yml",
    "Crypto CI": "crypto-ci.yml", "CodeQL": "codeql.yml",
    "Secret Hygiene": "secret-hygiene.yml", "Docs CI": "docs-ci.yml",
}


def glob_matches(value, pattern):
    """GitHub path globs: * excludes /; ** includes it; preserve pattern order."""
    expression = ""
    i = 0
    while i < len(pattern):
        if pattern[i:i + 3] == "**/":
            expression += "(?:.*/)?"
            i += 3
        elif pattern[i:i + 2] == "**":
            expression += ".*"
            i += 2
        elif pattern[i] == "*":
            expression += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            expression += "[^/]"
            i += 1
        elif pattern[i] in "[]+":
            raise ValueError("Unsupported workflow glob; review release gate before activation")
        else:
            expression += re.escape(pattern[i])
            i += 1
    return re.fullmatch(expression, value) is not None


def matches_patterns(value, patterns):
    if not isinstance(patterns, list) or not all(isinstance(p, str) and p for p in patterns):
        raise ValueError("Invalid workflow filters")
    matched = False
    for pattern in patterns:
        excluded = pattern.startswith("!")
        if glob_matches(value, pattern[1:] if excluded else pattern):
            matched = not excluded
    return matched


def expected_core(files, workflow_dir=Path(".github/workflows")):
    # Secret hygiene is mandatory even if its trigger is accidentally narrowed.
    required = {"Secret Hygiene"}
    for name, filename in WORKFLOWS.items():
        document = yaml.safe_load((workflow_dir / filename).read_text(encoding="utf-8"))
        if document.get("name") != name:
            raise ValueError(f"Release workflow name changed: {filename}")
        # PyYAML's YAML 1.1 loader treats the unquoted key `on` as True.
        events = document.get("on", document.get(True))
        if not isinstance(events, dict):
            raise ValueError(f"Unsupported workflow trigger: {filename}")
        if "push" not in events:
            continue
        push = events["push"] or {}
        if not isinstance(push, dict):
            raise ValueError(f"Unsupported push trigger: {filename}")
        if "branches" in push and not matches_patterns("master", push["branches"]):
            continue
        if "branches-ignore" in push and matches_patterns("master", push["branches-ignore"]):
            continue
        if "paths" in push and not any(matches_patterns(path, push["paths"]) for path in files):
            continue
        if "paths-ignore" in push and all(matches_patterns(path, push["paths-ignore"]) for path in files):
            continue
        required.add(name)
    return required


def ci_state(runs, sha, required):
    selected = {}
    for run in runs:  # GitHub returns newest runs first; do not accept an older rerun.
        name = run.get("name")
        if run.get("head_sha") == sha and run.get("event") == "push" and name in BLOCKING:
            selected.setdefault(name, run)
    missing = sorted(required - selected.keys())
    failed = {name: run.get("conclusion") for name, run in selected.items()
              if run.get("status") == "completed" and run.get("conclusion") != "success"}
    pending = sorted(name for name, run in selected.items() if run.get("status") != "completed")
    return {"missing": missing, "failed": failed, "pending": pending,
            "ready": not missing and not failed and not pending}


def api(repo, suffix):
    response = subprocess.run(["gh", "api", f"repos/{repo}/{suffix}"], capture_output=True,
                              text=True, check=True, timeout=60)
    return json.loads(response.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--before", default="")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo) or not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        raise SystemExit("Invalid release repository or SHA")
    if args.before and args.before != "0" * 40:
        if not re.fullmatch(r"[0-9a-f]{40}", args.before):
            raise SystemExit("Invalid previous SHA")
        change = api(args.repo, f"compare/{args.before}...{args.sha}")
    else:
        change = api(args.repo, f"commits/{args.sha}")
    files = change.get("files", [])
    if not files or len(files) >= 300:
        raise SystemExit("Release change set missing or too large to verify")
    required = expected_core([item["filename"] for item in files])
    start = time.monotonic()
    previous = None
    while time.monotonic() - start < args.timeout:
        runs = api(args.repo, f"actions/runs?head_sha={args.sha}&event=push&per_page=100")["workflow_runs"]
        state = ci_state(runs, args.sha, required)
        if state != previous:
            print(json.dumps({"sha": args.sha, **state}), flush=True)
            previous = state
        if state["failed"]:
            raise SystemExit("Release blocked by failed/cancelled CI; production was not activated")
        if state["ready"]:
            return
        if state["missing"] and time.monotonic() - start > 90:
            raise SystemExit("Required release CI did not start; refusing activation")
        time.sleep(15)
    raise SystemExit("Release CI deadline exceeded; refusing activation")


if __name__ == "__main__":
    main()
