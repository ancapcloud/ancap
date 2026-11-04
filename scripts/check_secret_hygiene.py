from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PATTERN_PATHS = {
    Path("MASTER_ROADMAP.md"),
}
TOKEN_PATTERNS: tuple[tuple[bytes, str], ...] = (
    (b"sk" + b"-aw-", "provider API key pattern"),
    (b"sk" + b"-prod-", "provider production API key pattern"),
    (b"sk" + b"-proj-", "OpenAI project API key pattern"),
    (b"sk" + b"-svcacct-", "OpenAI service account API key pattern"),
    (b"sk" + b"-ant-", "Anthropic API key pattern"),
    (b"sk_" + b"live_", "Stripe live secret key pattern"),
    (b"pk_" + b"live_", "Stripe live publishable key pattern"),
    (b"rk_" + b"live_", "Stripe live restricted key pattern"),
    (b"wh" + b"sec_", "Stripe webhook secret pattern"),
    (b"gh" + b"p_", "GitHub personal access token pattern"),
    (b"gh" + b"s_", "GitHub server token pattern"),
    (b"gh" + b"o_", "GitHub OAuth token pattern"),
    (b"github" + b"_pat_", "GitHub fine-grained personal access token pattern"),
    (b"gh" + b"u_", "GitHub user-to-server token pattern"),
    (b"gh" + b"r_", "GitHub refresh token pattern"),
)

# Platform-issued credentials have no fixed vendor prefix that is safe to grep
# for ("ancap_" is also a common identifier prefix), so match the generated
# shape: "ancap_" + secrets.token_urlsafe(24) (32 URL-safe chars) with mixed
# character classes that snake_case identifiers do not have.
_ANCAP_KEY_RE = re.compile(rb"(?<![A-Za-z0-9_])ancap_[A-Za-z0-9_-]{32}(?![A-Za-z0-9_-])")
REGEX_PATTERNS: tuple[tuple[re.Pattern[bytes], str], ...] = (
    (_ANCAP_KEY_RE, "ANCAP platform API key"),
)


def _looks_like_generated_token(candidate: bytes) -> bool:
    body = candidate[len(b"ancap_"):]
    return (
        any(c in b"ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in body)
        and any(c in b"abcdefghijklmnopqrstuvwxyz" for c in body)
        and any(c in b"0123456789" for c in body)
    )


def _regex_findings(line: bytes) -> list[str]:
    labels: list[str] = []
    for pattern, label in REGEX_PATTERNS:
        if any(_looks_like_generated_token(m.group(0)) for m in pattern.finditer(line)):
            labels.append(label)
    return labels


@dataclass(frozen=True)
class SecretMatch:
    path: Path
    line_number: int
    label: str
    line: str
    source_ref: str | None = None


@dataclass(frozen=True)
class SecretScanReport:
    ok: bool
    repo_root: str
    head_ref: str | None
    head_commit: str | None
    working_tree_dirty: bool
    include_untracked: bool
    staged_only: bool
    pending_push: bool
    history_range: str | None
    recent_history_count: int | None
    history_scope: str | None
    tracked_files_scanned: int
    untracked_files_scanned: int
    staged_files_scanned: int
    history_commits_scanned: int
    allowed_paths: list[str]
    findings: list[SecretMatch]


def _decode_git_paths(output: bytes) -> list[Path]:
    files: list[Path] = []
    for raw_path in output.split(b"\x00"):
        if not raw_path:
            continue
        files.append(Path(raw_path.decode("utf-8", errors="surrogateescape")))
    return files


def _git_ls_files(repo_root: Path, *args: str) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return _decode_git_paths(result.stdout)


def _git_diff_paths(repo_root: Path, *args: str) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "-z", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return _decode_git_paths(result.stdout)


def tracked_files(repo_root: Path) -> list[Path]:
    return _git_ls_files(repo_root)


def untracked_files(repo_root: Path) -> list[Path]:
    return _git_ls_files(repo_root, "--others", "--exclude-standard")


def staged_files(repo_root: Path) -> list[Path]:
    return _git_diff_paths(repo_root, "--cached", "--name-only", "--diff-filter=ACMRT")


def history_commits(repo_root: Path, rev_range: str) -> list[str]:
    result = subprocess.run(
        ["git", "rev-list", "--reverse", rev_range],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def optional_history_commits(repo_root: Path, rev_range: str) -> list[str] | None:
    result = subprocess.run(
        ["git", "rev-list", "--reverse", rev_range],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _git_has_commits(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0



def current_head_commit(repo_root: Path) -> str | None:
    if not _git_has_commits(repo_root):
        return None
    return _git_optional_text(repo_root, "rev-parse", "HEAD")



def current_head_ref(repo_root: Path) -> str | None:
    if not _git_has_commits(repo_root):
        return None
    return _git_optional_text(repo_root, "rev-parse", "--abbrev-ref", "HEAD")



def working_tree_dirty(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())



def recent_history_commits(repo_root: Path, count: int, *, ref: str = "HEAD") -> list[str]:
    if not _git_has_commits(repo_root):
        return []

    result = subprocess.run(
        ["git", "rev-list", "--reverse", f"--max-count={count}", ref],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _git_optional_text(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def upstream_ref(repo_root: Path) -> str | None:
    return _git_optional_text(
        repo_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    )


def configured_upstream_ref(repo_root: Path) -> str | None:
    branch_name = _git_optional_text(repo_root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch_name or branch_name == "HEAD":
        return None

    remote_name = _git_optional_text(repo_root, "config", "--get", f"branch.{branch_name}.remote")
    merge_ref = _git_optional_text(repo_root, "config", "--get", f"branch.{branch_name}.merge")
    if not remote_name or not merge_ref or not merge_ref.startswith("refs/heads/"):
        return None

    return f"{remote_name}/{merge_ref.removeprefix('refs/heads/')}"


def default_remote_head_ref(repo_root: Path) -> str | None:
    return _git_optional_text(repo_root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")


def resolve_pending_push_history(
    repo_root: Path,
    *,
    fallback_count: int = 20,
) -> tuple[str | None, int | None, str, list[str]]:
    tracked_upstream = upstream_ref(repo_root)
    configured_tracked_upstream = configured_upstream_ref(repo_root)
    default_remote_reason = "no branch upstream configured"
    if tracked_upstream:
        pending_range = f"{tracked_upstream}..HEAD"
        commits = optional_history_commits(repo_root, pending_range)
        if commits is not None:
            return (
                pending_range,
                None,
                f"pending-push history range {pending_range}",
                commits,
            )
        default_remote_reason = f"tracked upstream {tracked_upstream} unavailable locally"
    elif configured_tracked_upstream:
        default_remote_reason = f"tracked upstream {configured_tracked_upstream} unavailable locally"

    remote_head = default_remote_head_ref(repo_root)
    if remote_head:
        pending_range = f"{remote_head}..HEAD"
        commits = optional_history_commits(repo_root, pending_range)
        if commits is not None:
            return (
                pending_range,
                None,
                f"pending-push history range {pending_range} ({default_remote_reason})",
                commits,
            )

    fallback_reason = "no upstream/default-remote base found"
    if default_remote_reason != "no branch upstream configured":
        fallback_reason = f"{default_remote_reason}; default-remote base unavailable locally"
    recent_commits = recent_history_commits(repo_root, fallback_count)
    return (
        None,
        fallback_count,
        f"pending-push fallback recent history window (up to {fallback_count} commits from HEAD; {fallback_reason})",
        recent_commits,
    )


def repo_files(repo_root: Path, *, include_untracked: bool = False) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    collections = [tracked_files(repo_root)]
    if include_untracked:
        collections.append(untracked_files(repo_root))

    for collection in collections:
        for relative_path in collection:
            if relative_path in seen:
                continue
            seen.add(relative_path)
            files.append(relative_path)
    return files


def _redact_token_like_substrings(line: str) -> str:
    redacted = line
    for prefix, _label in TOKEN_PATTERNS:
        prefix_text = prefix.decode("utf-8")
        redacted = re.sub(
            re.escape(prefix_text) + r"[A-Za-z0-9._-]*",
            prefix_text + "<redacted>",
            redacted,
        )
    redacted = re.sub(r"ancap_[A-Za-z0-9_-]{32}", "ancap_<redacted>", redacted)
    return redacted

def _format_line_snippet(line: bytes) -> str:
    snippet = _redact_token_like_substrings(line.decode("utf-8", errors="replace").strip())
    if len(snippet) > 180:
        snippet = snippet[:177] + "..."
    return snippet

def _scan_line_bytes(
    relative_path: Path,
    line_number: int,
    line: bytes,
    *,
    source_ref: str | None = None,
) -> list[SecretMatch]:
    if relative_path in ALLOWED_PATTERN_PATHS:
        return []

    matches: list[SecretMatch] = []
    for pattern, label in TOKEN_PATTERNS:
        if pattern in line:
            matches.append(
                SecretMatch(
                    path=relative_path,
                    line_number=line_number,
                    label=label,
                    line=_format_line_snippet(line),
                    source_ref=source_ref,
                )
            )
    for label in _regex_findings(line):
        matches.append(
            SecretMatch(
                path=relative_path,
                line_number=line_number,
                label=label,
                line=_format_line_snippet(line),
                source_ref=source_ref,
            )
        )
    return matches


def _scan_file_bytes(relative_path: Path, file_bytes: bytes, *, source_ref: str | None = None) -> list[SecretMatch]:
    if relative_path in ALLOWED_PATTERN_PATHS:
        return []

    if b"\x00" in file_bytes:
        return []

    matches: list[SecretMatch] = []
    for line_number, line in enumerate(file_bytes.splitlines(), start=1):
        matches.extend(_scan_line_bytes(relative_path, line_number, line, source_ref=source_ref))
    return matches


def _git_show_index_bytes(repo_root: Path, relative_path: Path) -> bytes:
    result = subprocess.run(
        ["git", "show", f":{relative_path.as_posix()}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return result.stdout



def scan_file(repo_root: Path, relative_path: Path) -> list[SecretMatch]:
    try:
        file_bytes = (repo_root / relative_path).read_bytes()
    except FileNotFoundError:
        # Keep the default tracked-files scan honest for tracked-but-currently-missing
        # paths: fall back to the git index so local deletions do not hide still-tracked
        # leaks or crash the scan.
        file_bytes = _git_show_index_bytes(repo_root, relative_path)
    return _scan_file_bytes(relative_path, file_bytes)


def scan_staged_file(repo_root: Path, relative_path: Path) -> list[SecretMatch]:
    return _scan_file_bytes(relative_path, _git_show_index_bytes(repo_root, relative_path))


def scan_history_commit(repo_root: Path, commit: str) -> list[SecretMatch]:
    pattern_args: list[str] = []
    for prefix, _label in TOKEN_PATTERNS:
        pattern_args.extend(["-e", prefix.decode("utf-8")])

    result = subprocess.run(
        ["git", "grep", "-n", "-I", "--full-name", *pattern_args, commit, "--"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        result.check_returncode()

    findings: list[SecretMatch] = []
    for raw_line in result.stdout.splitlines():
        source_ref, path_text, line_number_text, line_text = raw_line.split(":", 3)
        findings.extend(
            _scan_line_bytes(
                Path(path_text),
                int(line_number_text),
                line_text.encode("utf-8", errors="replace"),
                source_ref=source_ref,
            )
        )
    return findings


def scan_paths(repo_root: Path, paths: list[Path]) -> list[SecretMatch]:
    findings: list[SecretMatch] = []
    for relative_path in paths:
        findings.extend(scan_file(repo_root, relative_path))
    return findings


def scan_staged_paths(repo_root: Path, paths: list[Path]) -> list[SecretMatch]:
    findings: list[SecretMatch] = []
    for relative_path in paths:
        findings.extend(scan_staged_file(repo_root, relative_path))
    return findings


def scan_history_range(repo_root: Path, commits: list[str]) -> list[SecretMatch]:
    findings: list[SecretMatch] = []
    for commit in commits:
        findings.extend(scan_history_commit(repo_root, commit))
    return findings


def scan_repo(repo_root: Path, *, include_untracked: bool = False, staged_only: bool = False) -> list[SecretMatch]:
    if staged_only:
        return scan_staged_paths(repo_root, staged_files(repo_root))
    return scan_paths(repo_root, repo_files(repo_root, include_untracked=include_untracked))


def build_report(
    repo_root: Path,
    *,
    include_untracked: bool,
    staged_only: bool,
    pending_push: bool,
    history_range: str | None,
    recent_history_count: int | None,
    history_scope: str | None,
    history_commits_scanned: int,
    scanned_paths: list[Path],
    findings: list[SecretMatch],
) -> SecretScanReport:
    tracked_count = 0 if staged_only or history_scope else len(tracked_files(repo_root))
    untracked_count = len(untracked_files(repo_root)) if include_untracked else 0
    staged_count = len(scanned_paths) if staged_only else 0
    return SecretScanReport(
        ok=not findings,
        repo_root=str(repo_root),
        head_ref=current_head_ref(repo_root),
        head_commit=current_head_commit(repo_root),
        working_tree_dirty=working_tree_dirty(repo_root),
        include_untracked=include_untracked,
        staged_only=staged_only,
        pending_push=pending_push,
        history_range=history_range,
        recent_history_count=recent_history_count,
        history_scope=history_scope,
        tracked_files_scanned=tracked_count,
        untracked_files_scanned=untracked_count,
        staged_files_scanned=staged_count,
        history_commits_scanned=history_commits_scanned,
        allowed_paths=sorted(path.as_posix() for path in ALLOWED_PATTERN_PATHS),
        findings=findings,
    )


def _scan_summary_parts(report: SecretScanReport) -> list[str]:
    parts: list[str] = []
    if report.tracked_files_scanned:
        parts.append(f"{report.tracked_files_scanned} tracked files scanned")
    if report.include_untracked or report.untracked_files_scanned:
        parts.append(f"{report.untracked_files_scanned} untracked files scanned")
    if report.staged_only or report.staged_files_scanned:
        parts.append(f"{report.staged_files_scanned} staged files scanned")
    if report.history_scope:
        parts.append(
            f"{report.history_commits_scanned} commits scanned from {report.history_scope}"
        )
    if report.head_commit:
        head_ref = report.head_ref or "HEAD"
        dirty_suffix = ", dirty working tree" if report.working_tree_dirty else ", clean working tree"
        parts.append(f"HEAD {head_ref}@{report.head_commit[:12]}{dirty_suffix}")
    return parts or ["0 files scanned"]


def _render_finding_location(finding: SecretMatch) -> str:
    if finding.source_ref:
        return f"{finding.source_ref}:{finding.path}:{finding.line_number}"
    return f"{finding.path}:{finding.line_number}"


def render_text_report(report: SecretScanReport) -> str:
    if report.ok:
        summary = "; ".join(_scan_summary_parts(report))
        allowed = ", ".join(report.allowed_paths) or "<none>"
        return f"Secret hygiene scan passed: {summary}; remediation-note allowlist: {allowed}."

    if report.history_scope:
        scope = report.history_scope
    else:
        scope = "staged files" if report.staged_only else "repo files"
    lines = [f"Secret hygiene scan failed. Unexpected token-shaped patterns found in {scope}:"]
    for finding in report.findings:
        lines.append(
            f"- {_render_finding_location(finding)}: {finding.label}: {finding.line}"
        )
    allowed = ", ".join(report.allowed_paths) or "<none>"
    lines.append(f"Allowed remediation-note paths: {allowed}")
    lines.append("Finding previews are redacted to avoid copying live secret values into logs/artifacts.")
    return "\n".join(lines)

def render_json_report(report: SecretScanReport) -> str:
    payload: dict[str, Any] = asdict(report)
    payload["findings"] = [
        {
            "path": finding.path.as_posix(),
            "line_number": finding.line_number,
            "label": finding.label,
            "line": finding.line,
            "source_ref": finding.source_ref,
        }
        for finding in report.findings
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

def emit_report(report_text: str, *, output_path: str | None, stream: Any) -> None:
    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(report_text, encoding="utf-8")
    print(report_text, file=stream, end="" if report_text.endswith("\n") else "\n")



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan repo files for token-shaped secret patterns.")
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument(
        "--include-untracked",
        action="store_true",
        help="Also scan untracked, non-ignored working-tree files in addition to tracked files.",
    )
    scope_group.add_argument(
        "--staged",
        action="store_true",
        help="Scan staged git-index content instead of the working tree so pre-commit leaks cannot hide behind later unstaged cleanup.",
    )
    scope_group.add_argument(
        "--history-range",
        help="Scan the full committed tree state for each commit in a git rev-range (for example HEAD~20..HEAD) so unchanged leaked files and later-cleaned secrets still surface anywhere inside that history window.",
    )
    scope_group.add_argument(
        "--recent-history",
        type=int,
        help="Scan up to the last N commits from HEAD without requiring HEAD~N to exist, which is safer for small or shallow local clones.",
    )
    scope_group.add_argument(
        "--pending-push",
        action="store_true",
        help="Scan the exact commit history about to leave the workstation: use the tracked branch upstream when available and still resolvable, otherwise fall back to origin/HEAD..HEAD or a recent-history window when no push base can be resolved.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the scan summary/report.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write the formatted report as UTF-8 in addition to stdout/stderr.",
    )
    args = parser.parse_args(argv)

    history_range = args.history_range
    if history_range is not None:
        history_range = history_range.strip()
        if not history_range:
            parser.error("--history-range requires a non-empty git rev-range, for example HEAD~20..HEAD")

    recent_history_count = args.recent_history
    if recent_history_count is not None and recent_history_count <= 0:
        parser.error("--recent-history requires a positive commit count")

    history_commits_scanned = 0
    history_scope: str | None = None
    pending_push = args.pending_push
    if history_range:
        commits = optional_history_commits(REPO_ROOT, history_range)
        if commits is None:
            parser.error(
                f"--history-range could not be resolved in this repo: {history_range}"
            )
        files: list[Path] = []
        findings = scan_history_range(REPO_ROOT, commits)
        history_commits_scanned = len(commits)
        history_scope = f"history range {history_range}"
    elif recent_history_count is not None:
        commits = recent_history_commits(REPO_ROOT, recent_history_count)
        files = []
        findings = scan_history_range(REPO_ROOT, commits)
        history_commits_scanned = len(commits)
        history_scope = f"recent history window (up to {recent_history_count} commits from HEAD)"
    elif pending_push:
        history_range, recent_history_count, history_scope, commits = resolve_pending_push_history(REPO_ROOT)
        files = []
        findings = scan_history_range(REPO_ROOT, commits)
        history_commits_scanned = len(commits)
    elif args.staged:
        files = staged_files(REPO_ROOT)
        findings = scan_staged_paths(REPO_ROOT, files)
    else:
        files = repo_files(REPO_ROOT, include_untracked=args.include_untracked)
        findings = scan_paths(REPO_ROOT, files)
    if history_scope is None and history_range:
        history_scope = f"history range {history_range}"
    report = build_report(
        REPO_ROOT,
        include_untracked=args.include_untracked,
        staged_only=args.staged,
        pending_push=pending_push,
        history_range=history_range,
        recent_history_count=recent_history_count,
        history_scope=history_scope,
        history_commits_scanned=history_commits_scanned,
        scanned_paths=files,
        findings=findings,
    )
    rendered = render_json_report(report) if args.format == "json" else render_text_report(report)

    if report.ok:
        emit_report(rendered, output_path=args.output, stream=sys.stdout)
        return 0

    emit_report(rendered, output_path=args.output, stream=sys.stderr if args.format == "text" else sys.stdout)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
