from __future__ import annotations

"""Generate paired markdown + JSON live-follow-up artifacts for the public ancap-docs repo."""

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SCRIPT = REPO_ROOT / "scripts" / "bootstrap_ancap_docs_repo.py"
DEFAULT_OUTPUT_DIR = Path("tmp")
DEFAULT_BASENAME = "ancap-docs-live-follow-up"
DEFAULT_LATEST_ALIAS_SUFFIX = "latest"


_bootstrap_spec = importlib.util.spec_from_file_location("bootstrap_ancap_docs_repo", BOOTSTRAP_SCRIPT)
assert _bootstrap_spec is not None and _bootstrap_spec.loader is not None
_bootstrap_module = importlib.util.module_from_spec(_bootstrap_spec)
_bootstrap_spec.loader.exec_module(_bootstrap_module)
validate_repo_argument = _bootstrap_module.validate_repo_argument


def _validate_filename_component(value: str, *, flag_name: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{flag_name} requires a non-empty value")
    if "/" in trimmed or "\\" in trimmed:
        raise ValueError(
            f"{flag_name} must be a filename component only, not a path: {trimmed}"
        )

    candidate = Path(trimmed)
    if candidate.name != trimmed or candidate.parent != Path("."):
        raise ValueError(
            f"{flag_name} must be a filename component only, not a path: {trimmed}"
        )
    if trimmed in {".", ".."}:
        raise ValueError(f"{flag_name} must not be '.' or '..'")
    return trimmed


def build_output_paths(*, output_dir: Path, basename: str, date_label: str) -> tuple[Path, Path]:
    stem = f"{basename}-{date_label}" if date_label else basename
    return output_dir / f"{stem}.md", output_dir / f"{stem}.json"


def build_latest_alias_paths(*, output_dir: Path, basename: str) -> tuple[Path, Path]:
    return (
        output_dir / f"{basename}-{DEFAULT_LATEST_ALIAS_SUFFIX}.md",
        output_dir / f"{basename}-{DEFAULT_LATEST_ALIAS_SUFFIX}.json",
    )


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _emit_completed_process(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")


def _emit_failure_context(*, label: str, result: subprocess.CompletedProcess[str]) -> None:
    print(f"{label} helper output:", file=sys.stderr)
    _emit_completed_process(result)


def _refresh_alias_artifact(*, source: Path, alias: Path) -> None:
    alias.write_bytes(source.read_bytes())


def _refresh_latest_alias_artifacts(
    *,
    markdown_output: Path,
    json_output: Path,
    markdown_alias: Path,
    json_alias: Path,
) -> None:
    _refresh_alias_artifact(source=markdown_output, alias=markdown_alias)
    _refresh_alias_artifact(source=json_output, alias=json_alias)


def _artifact_path_string(path: Path) -> str:
    return path.as_posix()


def _run_git_capture(*args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _current_repo_head_context() -> dict[str, object]:
    head_ref = _run_git_capture("symbolic-ref", "--quiet", "--short", "HEAD")
    head_commit = _run_git_capture("rev-parse", "HEAD")
    status_output = _run_git_capture("status", "--short")
    working_tree_dirty = bool(status_output) if status_output is not None else False
    return {
        "headRef": head_ref,
        "headCommit": head_commit,
        "workingTreeDirty": working_tree_dirty,
    }


def _validate_distinct_artifact_paths(
    *,
    markdown_output: Path,
    json_output: Path,
    markdown_alias: Path,
    json_alias: Path,
    write_latest_alias: bool,
) -> None:
    labeled_paths: list[tuple[str, Path]] = [
        ("dated markdown artifact", markdown_output),
        ("dated JSON artifact", json_output),
    ]
    if write_latest_alias:
        labeled_paths.extend(
            [
                ("latest markdown alias", markdown_alias),
                ("latest JSON alias", json_alias),
            ]
        )

    seen: dict[Path, str] = {}
    for label, path in labeled_paths:
        normalized = path.resolve(strict=False)
        prior_label = seen.get(normalized)
        if prior_label is not None:
            raise ValueError(
                f"Refusing to reuse the same path for the {prior_label} and {label}: "
                f"{_artifact_path_string(path)}. Choose a different --date-label or pass "
                "--no-write-latest-alias."
            )
        seen[normalized] = label


def _build_artifact_metadata(
    *,
    repo: str,
    basename: str,
    date_label: str,
    markdown_output: Path,
    json_output: Path,
    markdown_alias: Path,
    json_alias: Path,
    write_latest_alias: bool,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "repo": repo,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "dateLabel": date_label,
        "basename": basename,
        "generator": _artifact_path_string(Path(__file__).resolve().relative_to(REPO_ROOT)),
        "bootstrapScript": _artifact_path_string(BOOTSTRAP_SCRIPT.relative_to(REPO_ROOT)),
        "repoHead": _current_repo_head_context(),
        "artifacts": {
            "markdown": _artifact_path_string(markdown_output),
            "json": _artifact_path_string(json_output),
        },
        "latestAliases": None,
    }
    if write_latest_alias:
        metadata["latestAliases"] = {
            "markdown": _artifact_path_string(markdown_alias),
            "json": _artifact_path_string(json_alias),
        }
    return metadata


def _write_json_payload(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def _update_json_artifact_metadata(*, path: Path, artifact_metadata: dict[str, object]) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read JSON follow-up artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON follow-up artifact {path} must contain an object payload")
    payload["artifactMetadata"] = artifact_metadata
    _write_json_payload(path, payload)


def _append_markdown_artifact_metadata(*, path: Path, artifact_metadata: dict[str, object]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Failed to read markdown follow-up artifact {path}: {exc}") from exc

    dated_artifacts = artifact_metadata.get("artifacts")
    latest_aliases = artifact_metadata.get("latestAliases")
    if not isinstance(dated_artifacts, dict):
        raise ValueError("Artifact metadata must include an artifacts mapping")

    lines = [
        text.rstrip(),
        "",
        "## Artifact metadata",
        f"- Generated at (UTC): `{artifact_metadata['generatedAt']}`",
        f"- Date label: `{artifact_metadata['dateLabel']}`",
        f"- Generator: `{artifact_metadata['generator']}`",
        f"- Bootstrap source: `{artifact_metadata['bootstrapScript']}`",
    ]
    repo_head = artifact_metadata.get("repoHead")
    if isinstance(repo_head, dict):
        head_ref = repo_head.get("headRef") or "HEAD"
        head_commit = repo_head.get("headCommit")
        working_tree_dirty = bool(repo_head.get("workingTreeDirty"))
        if isinstance(head_commit, str) and head_commit:
            dirty_text = "dirty" if working_tree_dirty else "clean"
            lines.append(f"- Generator repo HEAD: `{head_ref}` @ `{head_commit}` ({dirty_text} working tree)")
        else:
            lines.append("- Generator repo HEAD: unavailable")
    lines.extend([
        f"- Dated markdown artifact: `{dated_artifacts['markdown']}`",
        f"- Dated JSON artifact: `{dated_artifacts['json']}`",
    ])
    if isinstance(latest_aliases, dict):
        lines.extend(
            [
                f"- Latest markdown alias: `{latest_aliases['markdown']}`",
                f"- Latest JSON alias: `{latest_aliases['json']}`",
            ]
        )
    else:
        lines.append("- Latest aliases: not written (`--no-write-latest-alias`)")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _load_json_summary(path: Path) -> tuple[bool, int, int, dict[str, int], dict[str, dict[str, object]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to read JSON follow-up artifact {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"JSON follow-up artifact {path} must contain an object payload")

    overall_ok = payload.get("ok")
    drift_count = payload.get("driftCount")
    unknown_count = payload.get("unknownCount")
    if not isinstance(overall_ok, bool):
        raise ValueError(f"JSON follow-up artifact {path} is missing boolean 'ok'")
    if not isinstance(drift_count, int):
        raise ValueError(f"JSON follow-up artifact {path} is missing integer 'driftCount'")
    if not isinstance(unknown_count, int):
        raise ValueError(f"JSON follow-up artifact {path} is missing integer 'unknownCount'")

    drift_count_by_scope: dict[str, int] = {}
    drift_summary = payload.get("driftSummary")
    if drift_summary is not None:
        if not isinstance(drift_summary, dict):
            raise ValueError(f"JSON follow-up artifact {path} has invalid 'driftSummary'")
        raw_drift_count_by_scope = drift_summary.get("driftCountByScope", {})
        if not isinstance(raw_drift_count_by_scope, dict) or any(
            not isinstance(scope, str) or not isinstance(count, int)
            for scope, count in raw_drift_count_by_scope.items()
        ):
            raise ValueError(f"JSON follow-up artifact {path} has invalid 'driftSummary.driftCountByScope'")
        drift_count_by_scope = {
            scope: count
            for scope, count in raw_drift_count_by_scope.items()
            if count > 0
        }

    manual_follow_up_summary: dict[str, dict[str, object]] = {}
    raw_manual_follow_up_summary = payload.get("manualFollowUpSummary")
    if raw_manual_follow_up_summary is not None:
        if not isinstance(raw_manual_follow_up_summary, dict):
            raise ValueError(f"JSON follow-up artifact {path} has invalid 'manualFollowUpSummary'")
        for bucket_name, bucket_payload in raw_manual_follow_up_summary.items():
            if not isinstance(bucket_name, str) or not isinstance(bucket_payload, dict):
                raise ValueError(f"JSON follow-up artifact {path} has invalid manual-follow-up bucket data")
            count = bucket_payload.get("count")
            by_kind = bucket_payload.get("byKind", {})
            if not isinstance(count, int):
                raise ValueError(
                    f"JSON follow-up artifact {path} has invalid 'manualFollowUpSummary.{bucket_name}.count'"
                )
            if not isinstance(by_kind, dict) or any(
                not isinstance(kind, str) or not isinstance(kind_count, int)
                for kind, kind_count in by_kind.items()
            ):
                raise ValueError(
                    f"JSON follow-up artifact {path} has invalid 'manualFollowUpSummary.{bucket_name}.byKind'"
                )
            manual_follow_up_summary[bucket_name] = {
                "count": count,
                "byKind": by_kind,
            }

    return overall_ok, drift_count, unknown_count, drift_count_by_scope, manual_follow_up_summary


def _format_named_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))


def _build_manual_follow_up_summary_lines(manual_follow_up_summary: dict[str, dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for bucket_name, bucket_payload in manual_follow_up_summary.items():
        count = bucket_payload.get("count")
        by_kind = bucket_payload.get("byKind")
        if not isinstance(count, int) or count <= 0:
            continue
        detail = ""
        if isinstance(by_kind, dict) and by_kind:
            detail = f" ({_format_named_counts(by_kind)})"
        lines.append(f"{bucket_name}: {count}{detail}")
    return lines


def _summary_exit_code(*, overall_ok: bool, fail_on_not_ok: bool) -> int:
    if fail_on_not_ok and not overall_ok:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the paired markdown + JSON ancap-docs live follow-up artifacts from "
            "scripts/bootstrap_ancap_docs_repo.py --verify-live --verify-live-community."
        )
    )
    parser.add_argument("--repo", required=True, help="GitHub repository in OWNER/REPO format")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory for the paired artifacts (default: {DEFAULT_OUTPUT_DIR.as_posix()}).",
    )
    parser.add_argument(
        "--basename",
        default=DEFAULT_BASENAME,
        help=f"Artifact basename before the date suffix (default: {DEFAULT_BASENAME}).",
    )
    parser.add_argument(
        "--date-label",
        default=date.today().isoformat(),
        help="Date suffix to append to the artifact filenames (default: today in YYYY-MM-DD).",
    )
    parser.add_argument(
        "--verbose-child-output",
        action="store_true",
        help=(
            "Echo the underlying bootstrap helper stdout/stderr after each artifact is written. "
            "By default this wrapper keeps terminal output concise and relies on the saved files for the full checklist/payload."
        ),
    )
    parser.add_argument(
        "--write-latest-alias",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Also refresh stable latest-alias files <basename>-latest.md and <basename>-latest.json "
            "alongside the dated outputs (default: true). Use --no-write-latest-alias when only the dated artifacts should be written."
        ),
    )
    parser.add_argument(
        "--fail-on-not-ok",
        action="store_true",
        help=(
            "Return exit code 2 when the generated JSON summary reports ok=false "
            "(for example when drift or unknown checks remain). Useful for cron/CI drift alarms without parsing the saved JSON by hand."
        ),
    )
    parser.add_argument(
        "--bootstrap-script",
        default=str(BOOTSTRAP_SCRIPT),
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    try:
        args.repo = validate_repo_argument(args.repo)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    basename = ""
    date_label = ""
    try:
        basename = _validate_filename_component(args.basename, flag_name="--basename")
        date_label = _validate_filename_component(args.date_label, flag_name="--date-label")
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    bootstrap_script = Path(args.bootstrap_script)
    if not bootstrap_script.exists():
        parser.error(f"--bootstrap-script does not exist: {bootstrap_script}")
    if not bootstrap_script.is_file():
        parser.error(f"--bootstrap-script must point to a file: {bootstrap_script}")

    output_dir = Path(args.output_dir)
    if output_dir.exists() and not output_dir.is_dir():
        parser.error(f"--output-dir must be a directory path: {output_dir}")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        parser.error(f"failed to create --output-dir {output_dir}: {exc}")

    markdown_output, json_output = build_output_paths(
        output_dir=output_dir,
        basename=basename,
        date_label=date_label,
    )
    markdown_latest_alias, json_latest_alias = build_latest_alias_paths(
        output_dir=output_dir,
        basename=basename,
    )
    try:
        _validate_distinct_artifact_paths(
            markdown_output=markdown_output,
            json_output=json_output,
            markdown_alias=markdown_latest_alias,
            json_alias=json_latest_alias,
            write_latest_alias=args.write_latest_alias,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    common_command = [
        sys.executable,
        str(bootstrap_script),
        "--repo",
        args.repo,
        "--verify-live",
        "--verify-live-community",
    ]

    artifact_commands = [
        ("markdown", markdown_output, common_command + ["--format", "markdown", "--output", str(markdown_output)]),
        ("json", json_output, common_command + ["--format", "json", "--output", str(json_output)]),
    ]

    for label, output_path, command in artifact_commands:
        print(f"Generating {label} follow-up artifact: {output_path}")
        result = _run_command(command)
        if result.returncode != 0:
            _emit_failure_context(label=label, result=result)
            print(f"Failed to generate {label} follow-up artifact.", file=sys.stderr)
            return result.returncode or 1
        if not output_path.exists():
            _emit_failure_context(label=label, result=result)
            print(f"Expected {label} artifact was not written: {output_path}", file=sys.stderr)
            return 1
        if args.verbose_child_output:
            _emit_completed_process(result)

    artifact_metadata = _build_artifact_metadata(
        repo=args.repo,
        basename=basename,
        date_label=date_label,
        markdown_output=markdown_output,
        json_output=json_output,
        markdown_alias=markdown_latest_alias,
        json_alias=json_latest_alias,
        write_latest_alias=args.write_latest_alias,
    )
    try:
        _append_markdown_artifact_metadata(path=markdown_output, artifact_metadata=artifact_metadata)
        _update_json_artifact_metadata(path=json_output, artifact_metadata=artifact_metadata)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.write_latest_alias:
        try:
            _refresh_latest_alias_artifacts(
                markdown_output=markdown_output,
                json_output=json_output,
                markdown_alias=markdown_latest_alias,
                json_alias=json_latest_alias,
            )
        except OSError as exc:
            print(f"Failed to refresh latest-alias artifacts: {exc}", file=sys.stderr)
            return 1

    try:
        overall_ok, drift_count, unknown_count, drift_count_by_scope, manual_follow_up_summary = _load_json_summary(json_output)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Live follow-up summary:")
    print(f"- Overall OK: {overall_ok}")
    print(f"- Drift count: {drift_count}")
    print(f"- Unknown count: {unknown_count}")
    if drift_count_by_scope:
        print("- Drift by scope:")
        for scope, count in sorted(drift_count_by_scope.items()):
            print(f"  - {scope}: {count}")
    manual_follow_up_lines = _build_manual_follow_up_summary_lines(manual_follow_up_summary)
    if manual_follow_up_lines:
        print("- Manual follow-up counts:")
        for line in manual_follow_up_lines:
            print(f"  - {line}")
    print("Saved paired ancap-docs live follow-up artifacts:")
    print(f"- {markdown_output}")
    print(f"- {json_output}")
    if args.write_latest_alias:
        print("Saved stable latest-alias artifacts:")
        print(f"- {markdown_latest_alias}")
        print(f"- {json_latest_alias}")

    exit_code = _summary_exit_code(overall_ok=overall_ok, fail_on_not_ok=args.fail_on_not_ok)
    if exit_code != 0:
        print(
            "Live follow-up summary is not OK; exiting non-zero because --fail-on-not-ok was requested.",
            file=sys.stderr,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
