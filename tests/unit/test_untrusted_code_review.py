import importlib.util
import os
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[2] / "scripts/review_untrusted_code.py"
    spec = importlib.util.spec_from_file_location("untrusted_review", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_review_copy_excludes_credentials_and_build_hooks(tmp_path):
    review = module()
    source, stage = tmp_path / "assignment", tmp_path / "stage"
    source.mkdir()
    stage.mkdir()
    for name in ("main.py", ".env", "custodial.keystore.json", "ssh-private-key.txt"):
        (source / name).write_text("fixture")
    (source / "Sicret").mkdir()
    (source / "Sicret/key.json").write_text("fixture")
    review.stage_sources(source, stage)
    assert [path.name for path in stage.iterdir()] == ["main.py"]
    command = review.container_command("sha256:" + "a" * 64, stage, "main.py", "fixture-review")
    for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pull=never", "--user=65534:65534"):
        assert flag in command
    assert "-e" not in command
    assert "/var/run/docker.sock" not in str(command)
    assert "python" in command and "-I" in command
    for entry in ("../main.py", "/main.py", "main.ps1"):
        with pytest.raises(ValueError):
            review.container_command("sha256:" + "a" * 64, stage, entry, "fixture")
    with pytest.raises(ValueError):
        review.container_command("python:latest", stage, "main.py", "fixture")


def test_review_does_not_follow_hardlinks(tmp_path):
    import os
    review = module()
    source, stage = tmp_path / "assignment", tmp_path / "stage"
    source.mkdir()
    stage.mkdir()
    private = tmp_path / "outside.txt"
    private.write_text("private-fixture")
    os.link(private, source / "innocent.txt")
    review.stage_sources(source, stage)
    assert list(stage.iterdir()) == []


def test_isolated_bootstrap_can_import_staged_sibling_modules(tmp_path):
    import subprocess
    import sys
    review = module()
    (tmp_path / "helper.py").write_text("VALUE = 42\n")
    entry = tmp_path / "main.py"
    entry.write_text("import helper; print(helper.VALUE)\n")
    command = review.container_command("sha256:" + "a" * 64, tmp_path, "main.py", "fixture")
    index = command.index("python")
    # Execute only the authored fixture with the actual guest bootstrap/flags.
    result = subprocess.run([sys.executable, *command[index + 1:-1], str(entry)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "42"


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory modes")
def test_nested_staging_is_traversable_with_private_umask(tmp_path):
    import stat
    review = module()
    source, stage = tmp_path / "assignment", tmp_path / "stage"
    (source / "pkg/sub").mkdir(parents=True)
    (source / "pkg/sub/main.py").write_text("print('nested')\n")
    stage.mkdir(mode=0o700)
    previous = os.umask(0o077)
    try:
        review.stage_sources(source, stage)
    finally:
        os.umask(previous)
    for directory in (stage, stage / "pkg", stage / "pkg/sub"):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o755
    assert stat.S_IMODE((stage / "pkg/sub/main.py").stat().st_mode) == 0o644
