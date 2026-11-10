"""Exercise the real rootless host smoke without nginx changes or network access."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ensure-acp1-host-proxy.sh"


def bash_path(path):
    value = str(path).replace("\\", "/")
    return f"/mnt/{value[0].lower()}/{value[3:]}" if os.name == "nt" else value


def smoke(tmp_path, mode):
    if not shutil.which("bash"):
        pytest.skip("Bash is required for the deployment smoke")
    tools = tmp_path / "tools"
    tools.mkdir()
    for name, body in {
        "hostname": "printf '192.0.2.1\\n'\n",
        "ss": "exit 0\n",
        "curl": r'''
output=''
previous=''
for argument in "$@"; do
  if [[ "$previous" == '-o' ]]; then output="$argument"; fi
  previous="$argument"
done
printf '%s\n' "$*" >> "$SMOKE_TEST_DIR/calls.log"
kind=host
if [[ "${!#}" == *':8080/rpc' ]]; then kind=compose; fi
count_file="$SMOKE_TEST_DIR/$kind-count"
count=0
if [[ -f "$count_file" ]]; then read -r count < "$count_file"; fi
count=$((count + 1))
printf '%s\n' "$count" > "$count_file"
code=200
body='{"jsonrpc":"2.0","id":1,"result":21}'
if [[ "$kind" == host ]]; then
  case "$SMOKE_TEST_MODE" in
    delayed) if ((count == 1)); then code=404; body='<html>old worker</html>'; fi ;;
    down) code=404; body='<html>bad vhost</html>' ;;
    error) body='{"jsonrpc":"2.0","id":1,"error":{"code":-32603}}' ;;
    html) body='<html>default site</html>' ;;
    boolean) body='{"jsonrpc":"2.0","id":1,"result":true}' ;;
  esac
fi
if [[ "$SMOKE_TEST_MODE" == upstream-down && "$kind" == compose ]]; then code=503; fi
printf '%s' "$body" > "$output"
printf '%s' "$code"
''',
    }.items():
        file = tools / name
        file.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8", newline="\n")
        file.chmod(0o755)
    command = (
        f"export PATH={shlex.quote(bash_path(tools))}:\"$PATH\"; "
        f"export SMOKE_TEST_DIR={shlex.quote(bash_path(tmp_path))}; "
        f"export SMOKE_TEST_MODE={shlex.quote(mode)} ACP1_SMOKE_ATTEMPTS=2 ACP1_SMOKE_DELAY=0; "
        f"bash {shlex.quote(bash_path(SCRIPT))} --smoke-only\n"
    )
    env = {k: v for k, v in os.environ.items() if k not in ("BASH_ENV", "ENV")}
    result = subprocess.run(["bash", "-s"], input=command.encode(), env=env,
                            capture_output=True, timeout=45)
    return result, (tmp_path / "calls.log").read_text()


def test_reload_convergence_retries_then_accepts_both_routes(tmp_path):
    result, calls = smoke(tmp_path, "delayed")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "host-count").read_text().strip() == "2"
    assert "--resolve acp1.ancap.cloud:443:192.0.2.1" in calls
    assert "https://acp1.ancap.cloud/rpc" in calls
    assert "--noproxy *" in calls


@pytest.mark.parametrize("mode", ["down", "error", "html", "boolean", "upstream-down"])
def test_bad_route_or_invalid_rpc_still_fails_closed(tmp_path, mode):
    result, _ = smoke(tmp_path, mode)
    assert result.returncode == 1
    assert (tmp_path / "host-count").read_text().strip() == "2"
