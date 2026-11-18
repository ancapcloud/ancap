"""Exercise the actual build gate without Docker, secrets or production access."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/deploy-ancap-cloud.sh"


@pytest.mark.parametrize("full,failed_service", [(False, ""), (True, ""), (True, "frontend"), (True, "acp-node")])
def test_builds_are_serial_and_fail_closed(full, failed_service):
    bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
    if not bash or not Path(bash).is_file():
        pytest.skip("Bash is unavailable")
    source = SCRIPT.read_text(encoding="utf-8")
    build_gate = source.split('if [[ "$WITH_ACP_NODE" -eq 1 ]]; then', 1)[1].split('if [[ "$SKIP_MIG" -eq 0 ]]; then', 1)[0]
    build_gate = 'if [[ "$WITH_ACP_NODE" -eq 1 ]]; then' + build_gate
    bootstrap = r'''
set -euo pipefail
COMPOSE='/isolated test/docker-compose.prod.yml'
docker() {
  test "$1" = compose && test "$2" = -f && test "$3" = "$COMPOSE"
  test "$4" = build && test "$#" = 5
  printf 'BUILD %s\n' "$5"
  if [[ "$5" == "$FAILED_SERVICE" ]]; then return 17; fi
  return 0
}
'''
    result = subprocess.run([bash, "-c", bootstrap + build_gate + '\nprintf "ACTIVATE\\n"\n'],
                            env={**os.environ, "WITH_ACP_NODE": str(int(full)), "FAILED_SERVICE": failed_service},
                            capture_output=True, text=True, timeout=20)
    builds = [line.removeprefix("BUILD ") for line in result.stdout.splitlines() if line.startswith("BUILD ")]
    expected = ["api", "frontend"] + (["acp-node"] if full else [])
    if failed_service:
        expected = expected[:expected.index(failed_service) + 1]
        assert result.returncode == 17, result.stderr
        assert "ACTIVATE" not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        assert "ACTIVATE" in result.stdout
    assert builds == expected
