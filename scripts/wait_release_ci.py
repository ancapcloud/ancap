"""Fail closed until the same commit's applicable push CI has succeeded."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import time

BLOCKING = {"Backend CI", "Frontend CI", "Crypto CI", "CodeQL", "Secret Hygiene", "Docs CI"}


def expected_core(files):
    required = set()
    if any(path.startswith(("app/", "alembic/")) or path in {"requirements.in", "requirements.txt", "pyproject.toml"} for path in files):
        required.update({"Backend CI", "Frontend CI"})
    if any(path.startswith(("frontend-app/", "ancap-mobile/")) or path in {".github/workflows/frontend-ci.yml", "docker-compose.yml", "Dockerfile"} for path in files):
        required.add("Frontend CI")
    if any(path.startswith(("ACP-crypto/", "contracts/bridge-bsc/", "contracts/robinhood-racp/")) or path == ".github/workflows/crypto-ci.yml" for path in files):
        required.add("Crypto CI")
    if any(path.startswith(("infra/", "mcp-server/")) or path in {"Dockerfile", "docker-compose.prod.yml", ".github/workflows/backend-ci.yml", ".github/workflows/deploy-ancap-cloud.yml", "scripts/wait_release_ci.py"} for path in files):
        required.add("Backend CI")
    return required or {"Backend CI"}


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
