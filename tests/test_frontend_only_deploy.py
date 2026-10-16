"""Exercise deployment gates without touching Docker or a real checkout."""
import io
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/deploy-frontend-only.sh"


@pytest.mark.parametrize("failure", ["fetch", "reset"])
def test_failed_git_update_never_builds_or_restarts(failure):
    bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
    if not bash or not Path(bash).is_file():
        pytest.skip("Bash is unavailable")
    bootstrap = r'''
cd() { return 0; }
sleep() { return 0; }
timeout() { shift; "$@"; }
git() { if [[ "$1" == "$FAIL_GIT" ]]; then return 1; fi; return 0; }
docker() { echo UNEXPECTED_DOCKER_CALL; return 99; }
'''
    env = {**os.environ, "FAIL_GIT": failure}
    result = subprocess.run([bash, "-c", bootstrap + "\nsource " + shlex.quote(SCRIPT.as_posix())],
                            env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert "UNEXPECTED_DOCKER_CALL" not in result.stdout


@pytest.mark.parametrize(
    "html,status,build,expected",
    [
        ('<section id="smart-pay">', "ready", "abc1234", None),
        ('<section id="mcp">', "ready", "abc1234", 1),
        ('<section id="smart-pay">', "degraded", "abc1234", 1),
        ('<section id="smart-pay">', "ready", "oldbuild", 1),
        ('<section id="smart-pay">', "ready", None, 1),
    ],
)
def test_frontend_verification_rejects_incomplete_release(html, status, build, expected):
    source = SCRIPT.read_text(encoding="utf-8").split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    responses = {
        "/": html,
        "/api/v1/system/ready": json.dumps({"status": status}),
        "/internal/frontend-build": json.dumps({"NEXT_PUBLIC_APP_BUILD_ID": build}),
    }

    def open_response(request, timeout):
        assert request.host == "127.0.0.1:8080"
        assert request.get_header("Host") == "ancap.cloud"
        return io.BytesIO(responses[request.selector].encode())

    with patch("urllib.request.urlopen", side_effect=open_response), patch("sys.argv", ["verify", "abc1234"]):
        if expected is None:
            exec(compile(source, str(SCRIPT), "exec"), {})
        else:
            with pytest.raises(SystemExit) as error:
                exec(compile(source, str(SCRIPT), "exec"), {})
            assert error.value.code == expected
