#!/usr/bin/env python3
"""Deploy bridge snapshot fix + run migration and mining on ancap-server."""
from __future__ import annotations

import base64
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/ancap-migration/current"
HOT = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"

FILES = [
    "alembic/versions/055_bridge_snapshot_wacp_wei_numeric.py",
    "alembic/versions/056_merge_bridge_snapshot_and_api_keys_heads.py",
    "app/db/models.py",
    "app/schemas/bridge_rail.py",
    "app/api/routers/bridge_rail.py",
    "app/services/bridge_reconciliation.py",
    "app/schemas/wallets.py",
    "app/api/routers/wallet_acp.py",
]


def ssh(cmd: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "ConnectTimeout=20", "ancap-server", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tar_path = tmp.name
    with tarfile.open(tar_path, "w:gz") as tar:
        for rel in FILES:
            path = ROOT / rel
            if not path.is_file():
                print(f"Missing {path}", file=sys.stderr)
                return 1
            tar.add(path, arcname=rel.replace("\\", "/"))

    print("=== Upload patch tarball ===")
    with open(tar_path, "rb") as f:
        upload = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=20", "ancap-server", f"cd {REMOTE} && tar xzf -"],
            stdin=f,
            capture_output=True,
            timeout=120,
        )
    Path(tar_path).unlink(missing_ok=True)
    if upload.returncode != 0:
        print(upload.stderr, file=sys.stderr)
        return 1
    remote_script = f"""set -euo pipefail
cd {REMOTE}
docker compose -f docker-compose.prod.yml build api
echo "=== Alembic upgrade ==="
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade d4a7c2e91f0b
echo "=== Restart api ==="
docker compose -f docker-compose.prod.yml up -d api
sleep 8
echo "=== Jobs tick x8 ==="
for i in 1 2 3 4 5 6 7 8; do
  echo "-- tick $i --"
  docker compose -f docker-compose.prod.yml exec -T api sh -lc 'curl -sS -X POST http://127.0.0.1:8000/v1/system/jobs/tick -H "content-type: application/json" -H "X-Cron-Secret: $CRON_SECRET" -d "{{}}"' | head -c 400 || true
  echo
  docker compose -f docker-compose.prod.yml exec -T acp-node sh -lc 'curl -sf -H "User-Agent: ancap-backend/1.0" -H "Content-Type: application/json" -d "{{\\"jsonrpc\\":\\"2.0\\",\\"id\\":1,\\"method\\":\\"getblockcount\\",\\"params\\":{{}}}}" http://127.0.0.1:8545/rpc' || true
  echo
  sleep 15
done
echo "=== Balances ==="
for addr in {HOT} acp1qqla8waukrudkleau9n6gzj9c58ufyfxaulvwumm acp1qrpavez2tttvly2umdjz8jfsdu5yjqjftuyzmau5 acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz; do
  docker compose -f docker-compose.prod.yml exec -T api walletd balance --rpc http://acp-node:8545/rpc --address "$addr"
done
echo "=== Health ==="
docker compose -f docker-compose.prod.yml exec -T api curl -sf http://127.0.0.1:8000/v1/system/health || true
"""
    rb64 = base64.b64encode(remote_script.encode()).decode()
    print("=== Deploy on server ===")
    r2 = ssh(f"echo {rb64} | base64 -d | bash", timeout=900)
    print(r2.stdout)
    if r2.stderr:
        print(r2.stderr, file=sys.stderr)
    return r2.returncode


if __name__ == "__main__":
    raise SystemExit(main())
