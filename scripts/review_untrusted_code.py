"""Run an external Python assignment in a disposable Linux container, without credentials.

Only a filtered copy is mounted. Docker Desktop's Linux VM is required on Windows.
This does not make arbitrary host execution safe or defend against hypervisor exploits.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import uuid

_SKIP = {"sicret", "secrets", "node_modules", "venv", "__pycache__", "target", "dist"}
_EXTENSIONS = {".py", ".txt", ".md", ".json", ".csv", ".toml", ".yaml", ".yml", ".js", ".ts", ".html", ".css"}
_PRIVATE_NAMES = re.compile(r"(keystore|mnemonic|credential|private.?key|secret|password|token|wallet|id_rsa|id_ed25519)", re.I)


def stage_sources(source: Path, destination: Path) -> None:
    total = 0
    count = 0
    for current, dirs, files in os.walk(source, followlinks=False):
        parent = Path(current)
        dirs[:] = [name for name in dirs if not name.startswith(".") and name.lower() not in _SKIP
                   and not _is_link(parent / name)]
        count += len(dirs)
        if count > 2000:
            raise ValueError("Assignment exceeds the review directory limit")
        for name in files:
            path = parent / name
            if name.startswith(".") or _PRIVATE_NAMES.search(name) or path.suffix.lower() not in _EXTENSIONS:
                continue
            info = path.lstat()
            if _is_link(path) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                continue
            total += info.st_size
            count += 1
            if total > 16 * 1024 * 1024 or count > 2000:
                raise ValueError("Assignment exceeds the 16 MiB / 2000 file review limit")
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            # Copy bytes, not links, modes or host metadata. Never run setup/install hooks.
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or opened.st_ino != info.st_ino:
                    raise ValueError("Assignment changed during staging")
                data = stream.read(16 * 1024 * 1024 + 1)
            if len(data) != info.st_size:
                raise ValueError("Assignment changed during staging")
            target.write_bytes(data)
            target.chmod(0o644)


def _is_link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def container_command(image: str, stage: Path, entry: str, name: str) -> list[str]:
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
        raise ValueError("Use the immutable image ID of an already installed trusted Python image")
    entry_path = Path(entry)
    if entry_path.is_absolute() or ".." in entry_path.parts or entry_path.suffix != ".py":
        raise ValueError("Entry must be a relative .py file inside the assignment")
    if not (stage / entry_path).is_file():
        raise ValueError("Entry was not included in the filtered review copy")
    return ["docker", "run", "--pull=never", "--rm", "--name", name,
            "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--pids-limit=64", "--memory=512m", "--cpus=1", "--user=65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m", "--workdir=/tmp",
            "--mount", f"type=bind,src={stage},dst=/review,readonly",
            image, "python", "-I", "-B", "/review/" + entry_path.as_posix()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("entry")
    parser.add_argument("--image", required=True, help="Preinstalled trusted Python image ID: sha256:...")
    args = parser.parse_args(argv)
    source = args.source.resolve(strict=True)
    if not source.is_dir() or "," in str(source):
        parser.error("Source must be a directory")
    if shutil.which("docker") is None:
        parser.error("Docker Desktop with Linux containers is required; host execution is never a fallback")
    name = "ancap-review-" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="ancap-review-") as folder:
        stage = Path(folder)
        stage.chmod(0o755)
        stage_sources(source, stage)
        command = container_command(args.image, stage, args.entry, name)
        # No environment is forwarded into the container. The Docker CLI still
        # needs its normal host connection settings; they are not container env.
        output = bytearray()
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        def drain():
            assert process.stdout is not None
            while chunk := process.stdout.read(4096):
                output.extend(chunk[:max(0, 65536 - len(output))])
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            code = process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            code = 124
        finally:
            subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=15, check=False)
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            reader.join(timeout=5)
        # Escape terminal controls so untrusted output cannot inject UI sequences.
        print(bytes(output).decode("utf-8", errors="replace").encode("unicode_escape").decode("ascii"))
        return code


if __name__ == "__main__":
    raise SystemExit(main())
