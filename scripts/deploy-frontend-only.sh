#!/usr/bin/env bash
set -euo pipefail
cd /opt/ancap-migration/current
COMPOSE="docker compose -f docker-compose.prod.yml"

fetched=0
for attempt in 1 2 3 4 5; do
  if timeout 120 git fetch origin master; then
    fetched=1
    break
  fi
  echo "git fetch failed (attempt ${attempt}/5)"
  sleep 10
done
if [[ "$fetched" -ne 1 ]]; then
  echo "Failed to fetch master; refusing to deploy an old checkout." >&2
  exit 1
fi
git reset --hard origin/master
docker compose -f docker-compose.prod.yml config --quiet

export APP_BUILD_ID="$(git rev-parse --short HEAD)"
echo "APP_BUILD_ID=$APP_BUILD_ID"

echo "== build frontend"
timeout 900 $COMPOSE build frontend

echo "== restart frontend + proxy"
timeout 120 $COMPOSE up -d frontend proxy

echo "== verify homepage, readiness and deployed build through compose proxy"
verified=0
for attempt in 1 2 3 4 5 6; do
  if python3 - "$APP_BUILD_ID" <<'PY'
import json
import sys
import urllib.request

def get(path):
    request = urllib.request.Request(
        "http://127.0.0.1:8080" + path, headers={"Host": "ancap.cloud"}
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode()

try:
    if 'id="smart-pay"' not in get("/"):
        raise ValueError("homepage missing Smart Pay")
    if json.loads(get("/api/v1/system/ready"))["status"] != "ready":
        raise ValueError("API not ready")
    build = json.loads(get("/internal/frontend-build"))["NEXT_PUBLIC_APP_BUILD_ID"]
    if build != sys.argv[1]:
        raise ValueError(f"build mismatch: {build} != {sys.argv[1]}")
except Exception as error:
    print(f"Verification failed: {error}", file=sys.stderr)
    sys.exit(1)
PY
  then
    verified=1
    break
  fi
  sleep 5
done
if [[ "$verified" -ne 1 ]]; then
  echo "Frontend deployment verification failed." >&2
  exit 1
fi
echo "OK frontend build $APP_BUILD_ID and API readiness verified"
