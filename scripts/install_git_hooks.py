from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOOKS_PATH = ".githooks"
EXPECTED_HOOK_NAMES = ("pre-commit", "pre-push")


def _git_config_get(repo_root: Path, key: str) -> str | None:
    result = subprocess.run(
        ["git", "config", "--get", key],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _git_config_set(repo_root: Path, key: str, value: str) -> None:
    subprocess.run(
        ["git", "config", key, value],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _ensure_hook_is_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _expected_hook_files(repo_root: Path, hooks_path: str) -> list[Path]:
    hooks_dir = repo_root / Path(hooks_path)
    return [hooks_dir / hook_name for hook_name in EXPECTED_HOOK_NAMES]


def _ensure_expected_hooks_are_executable(paths: list[Path]) -> None:
    for path in paths:
        _ensure_hook_is_executable(path)


def _display_hooks_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    while len(normalized) > 1 and normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def _hooks_path_key(repo_root: Path, value: str) -> str:
    hook_path = Path(value)
    if not hook_path.is_absolute():
        hook_path = repo_root / hook_path
    return os.path.normcase(str(hook_path.resolve(strict=False)))


def _is_hook_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def check_git_hooks(*, repo_root: Path, hooks_path: str) -> int:
    normalized_hooks_path = _display_hooks_path(hooks_path)
    expected_hooks_key = _hooks_path_key(repo_root, hooks_path)
    hook_files = _expected_hook_files(repo_root, hooks_path)
    missing_hooks = [path for path in hook_files if not path.exists()]
    if missing_hooks:
        missing_text = ", ".join(str(path) for path in missing_hooks)
        print(
            "Git hooks are not correctly configured: expected tracked hook file(s) are missing: "
            f"{missing_text}",
            file=sys.stderr,
        )
        return 1

    current_hooks_path = _git_config_get(repo_root, "core.hooksPath")
    normalized_current = _hooks_path_key(repo_root, current_hooks_path) if current_hooks_path else None
    if normalized_current != expected_hooks_key:
        current_display = _display_hooks_path(current_hooks_path) if current_hooks_path else "<unset>"
        print(
            "Git hooks are not correctly configured: "
            f"core.hooksPath={current_display}, expected={normalized_hooks_path}",
            file=sys.stderr,
        )
        return 1

    if sys.platform != "win32":
        non_executable_hooks = [
            path.relative_to(repo_root).as_posix()
            for path in hook_files
            if not _is_hook_executable(path)
        ]
        if non_executable_hooks:
            print(
                "Git hooks are configured but not executable: " + ", ".join(non_executable_hooks),
                file=sys.stderr,
            )
            return 1

    print(f"Git hooks are correctly configured at {normalized_hooks_path}.")
    return 0


def install_git_hooks(*, repo_root: Path, hooks_path: str, force: bool, dry_run: bool) -> int:
    normalized_hooks_path = _display_hooks_path(hooks_path)
    expected_hooks_key = _hooks_path_key(repo_root, hooks_path)
    hook_files = _expected_hook_files(repo_root, hooks_path)
    missing_hooks = [path for path in hook_files if not path.exists()]
    if missing_hooks:
        missing_text = ", ".join(str(path) for path in missing_hooks)
        print(
            "Refusing to configure git hooks: expected tracked hook file(s) are missing: "
            f"{missing_text}",
            file=sys.stderr,
        )
        return 1

    current_hooks_path = _git_config_get(repo_root, "core.hooksPath")
    normalized_current = _hooks_path_key(repo_root, current_hooks_path) if current_hooks_path else None

    if normalized_current == expected_hooks_key:
        if not dry_run:
            _ensure_expected_hooks_are_executable(hook_files)
        print(f"Git hooks already point at {normalized_hooks_path}.")
        return 0

    if normalized_current and not force:
        current_display = _display_hooks_path(current_hooks_path)
        print(
            "Refusing to overwrite existing git hooksPath without --force: "
            f"current={current_display}, requested={normalized_hooks_path}",
            file=sys.stderr,
        )
        return 1

    if dry_run:
        action = "would update" if normalized_current else "would set"
        print(f"Dry run: {action} core.hooksPath to {normalized_hooks_path}.")
        return 0

    _git_config_set(repo_root, "core.hooksPath", normalized_hooks_path)
    _ensure_expected_hooks_are_executable(hook_files)
    verb = "Updated" if normalized_current else "Set"
    print(f"{verb} core.hooksPath to {normalized_hooks_path}.")
    for hook_file in hook_files:
        print(f"Enabled hook: {hook_file.relative_to(repo_root).as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Point local git hooks at the repo's tracked .githooks directory."
    )
    parser.add_argument(
        "--hooks-path",
        default=DEFAULT_HOOKS_PATH,
        help="Relative hooks directory to configure in local git config (default: .githooks).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing core.hooksPath value instead of refusing to change it.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without mutating local git config.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that local git config already points at the tracked hooks without changing it.",
    )
    args = parser.parse_args(argv)

    if args.check:
        if args.force or args.dry_run:
            parser.error("--check cannot be combined with --force or --dry-run")
        return check_git_hooks(repo_root=REPO_ROOT, hooks_path=args.hooks_path)

    return install_git_hooks(
        repo_root=REPO_ROOT,
        hooks_path=args.hooks_path,
        force=args.force,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
