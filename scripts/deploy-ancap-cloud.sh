#!/usr/bin/env bash
# Full stack refresh for ancap.cloud: rebuild Docker prod stack + Alembic.
# Run on the Linux host behind Cloudflare Tunnel from the ANCAP repo root.
# Usage: bash scripts/deploy-ancap-cloud.sh [--skip-git-pull] [--skip-migrations] [--skip-post-deploy-checks]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
COMPOSE="$ROOT/docker-compose.prod.yml"
DOTENV="$ROOT/.env"
test -f "$COMPOSE" || { echo "Missing $COMPOSE"; exit 1; }

import_dotenv_if_present() {
  local dotenv_path="$1"
  if [[ ! -f "$dotenv_path" ]]; then
    return 0
  fi

  while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
    local line="${raw_line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    if [[ ! "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]]; then
      continue
    fi

    local name="${BASH_REMATCH[1]}"
    local value="${BASH_REMATCH[2]}"

    value="${value%$'\r'}"
    if [[ ${#value} -ge 2 ]]; then
      local first_char="${value:0:1}"
      local last_char="${value: -1}"
      if [[ "$first_char" == '"' && "$last_char" == '"' ]]; then
        value="${value:1:${#value}-2}"
      elif [[ "$first_char" == "'" && "$last_char" == "'" ]]; then
        value="${value:1:${#value}-2}"
      fi
    fi

    if [[ -z "${!name:-}" ]]; then
      export "$name=$value"
    fi
  done < "$dotenv_path"

  echo "Loaded compose substitution secrets from: $dotenv_path"
}

invoke_proxy_json_get() {
  local path="$1"
  docker compose -f "$COMPOSE" exec -T proxy wget -qO- "http://127.0.0.1${path}"
}

wait_for_proxy_status() {
  local path="$1"
  local expected_status="$2"
  local label="$3"
  local attempts="${4:-30}"
  local delay_seconds="${5:-2}"
  local last_payload=""

  for ((attempt=1; attempt<=attempts; attempt++)); do
    if payload="$(invoke_proxy_json_get "$path" 2>/dev/null)"; then
      last_payload="$payload"
      if python3 - <<'PY' "$expected_status" "$payload"
import json, sys
expected = sys.argv[1]
payload = json.loads(sys.argv[2])
sys.exit(0 if payload.get("status") == expected else 1)
PY
      then
        printf '%s\n' "$payload"
        return 0
      fi
    fi

    if (( attempt < attempts )); then
      sleep "$delay_seconds"
    fi
  done

  echo "$label did not reach status '$expected_status' via http://127.0.0.1${path}. Last payload: ${last_payload:-<none>}" >&2
  return 1
}

assert_frontend_build_id() {
  local expected_build_id="$1"
  local attempts="${2:-30}"
  local delay_seconds="${3:-2}"
  local last_payload=""

  for ((attempt=1; attempt<=attempts; attempt++)); do
    if payload="$(invoke_proxy_json_get "/internal/frontend-build" 2>/dev/null)"; then
      last_payload="$payload"
      if python3 - <<'PY' "$expected_build_id" "$payload"
import json, sys
expected = sys.argv[1]
payload = json.loads(sys.argv[2])
sys.exit(0 if payload.get("NEXT_PUBLIC_APP_BUILD_ID") == expected else 1)
PY
      then
        printf '%s\n' "$payload"
        return 0
      fi
    fi

    if (( attempt < attempts )); then
      sleep "$delay_seconds"
    fi
  done

  echo "Frontend build id behind proxy did not match APP_BUILD_ID=$expected_build_id via http://127.0.0.1/internal/frontend-build. Last payload: ${last_payload:-<none>}" >&2
  return 1
}

import_dotenv_if_present "$DOTENV"

placeholder_like_secret() {
  local value="${1:-}"
  if [[ -z "$value" ]]; then
    return 1
  fi

  local normalized_value="${value,,}"
  for phrase in change dev-secret change-me changeme secret example placeholder; do
    if [[ "$normalized_value" == *"$phrase"* ]]; then
      return 0
    fi
  done

  return 1
}

REQUIRED_PROD_SECRETS=(DATABASE_URL POSTGRES_PASSWORD SECRET_KEY CURSOR_SECRET CRON_SECRET ACP_RPC_TOKEN)
BUNDLED_POSTGRES_DEFAULT_USER="postgres"
BUNDLED_POSTGRES_DEFAULT_DB="ancap"
MISSING=()
for name in "${REQUIRED_PROD_SECRETS[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    MISSING+=("$name")
  fi
done
if (( ${#MISSING[@]} > 0 )); then
  echo "Missing required production secrets for docker-compose.prod.yml: ${MISSING[*]}. Set them in $DOTENV or export them in the shell before running this deploy script." >&2
  exit 1
fi

for secret_name in SECRET_KEY CURSOR_SECRET CRON_SECRET; do
  secret_value="${!secret_name:-}"
  if placeholder_like_secret "$secret_value"; then
    echo "$secret_name still uses an insecure placeholder-like value. Set a real random secret before running this deploy script." >&2
    exit 1
  fi
done

BUNDLED_POSTGRES_DEFAULT_USER="post""gres"
BUNDLED_POSTGRES_DEFAULT_PASSWORD="post""gres"
if [[ "${DATABASE_URL,,}" == *"://${BUNDLED_POSTGRES_DEFAULT_USER}:${BUNDLED_POSTGRES_DEFAULT_PASSWORD}@"* ]]; then
  echo "DATABASE_URL still uses insecure bundled-db default credentials. Set a real database password before running this deploy script." >&2
  exit 1
fi

DATABASE_URL_NO_SCHEME="${DATABASE_URL#*://}"
if [[ "$DATABASE_URL_NO_SCHEME" == "$DATABASE_URL" ]]; then
  echo "DATABASE_URL is not a valid URI. Fix it before running this deploy script." >&2
  exit 1
fi

DATABASE_URL_AUTHORITY="${DATABASE_URL_NO_SCHEME%%/*}"
DATABASE_URL_CREDENTIALS=""
DATABASE_URL_HOSTPORT="$DATABASE_URL_AUTHORITY"
if [[ "$DATABASE_URL_AUTHORITY" == *"@"* ]]; then
  DATABASE_URL_CREDENTIALS="${DATABASE_URL_AUTHORITY%@*}"
  DATABASE_URL_HOSTPORT="${DATABASE_URL_AUTHORITY#*@}"
fi
DATABASE_URL_HOST="${DATABASE_URL_HOSTPORT%%[:?]*}"
DATABASE_URL_QUERY=""
if [[ "$DATABASE_URL" == *\?* ]]; then
  DATABASE_URL_QUERY="${DATABASE_URL#*\?}"
fi
HAS_SOCKET_HOST_QUERY=0
SOCKET_HOST_VALUE=""
if [[ -n "$DATABASE_URL_QUERY" ]]; then
  IFS='&' read -r -a DATABASE_URL_QUERY_PARTS <<< "$DATABASE_URL_QUERY"
  for query_part in "${DATABASE_URL_QUERY_PARTS[@]}"; do
    if [[ "$query_part" == host=* ]]; then
      SOCKET_HOST_VALUE_RAW="${query_part#host=}"
      printf -v SOCKET_HOST_VALUE '%b' "${SOCKET_HOST_VALUE_RAW//%/\\x}"
      HAS_SOCKET_HOST_QUERY=1
      break
    fi
  done
fi
if [[ -z "$DATABASE_URL_HOST" && "$HAS_SOCKET_HOST_QUERY" -eq 0 ]]; then
  echo "DATABASE_URL is not a valid URI. Fix it before running this deploy script." >&2
  exit 1
fi
DATABASE_URL_USERNAME=""
if [[ -n "$DATABASE_URL_CREDENTIALS" ]]; then
  if [[ "$DATABASE_URL_CREDENTIALS" == *:* ]]; then
    DATABASE_URL_USERNAME="${DATABASE_URL_CREDENTIALS%%:*}"
  else
    DATABASE_URL_USERNAME="$DATABASE_URL_CREDENTIALS"
  fi
  printf -v DATABASE_URL_USERNAME '%b' "${DATABASE_URL_USERNAME//%/\\x}"
fi

DATABASE_URL_PASSWORD=""
DATABASE_URL_PASSWORD_DECODED=""
if [[ -n "$DATABASE_URL_CREDENTIALS" && "$DATABASE_URL_CREDENTIALS" == *:* ]]; then
  DATABASE_URL_PASSWORD="${DATABASE_URL_CREDENTIALS#*:}"
fi

if [[ -n "$DATABASE_URL_PASSWORD" ]]; then
  printf -v DATABASE_URL_PASSWORD_DECODED '%b' "${DATABASE_URL_PASSWORD//%/\\x}"
  if [[ "${DATABASE_URL_PASSWORD_DECODED,,}" == "postgres" ]]; then
    echo "DATABASE_URL still uses the insecure postgres database password. Set a real database password before running this deploy script." >&2
    exit 1
  fi
  if placeholder_like_secret "$DATABASE_URL_PASSWORD_DECODED"; then
    echo "DATABASE_URL uses a placeholder-like database password. Set a real database password before running this deploy script." >&2
    exit 1
  fi
fi

DATABASE_URL_PATH_WITHOUT_QUERY="${DATABASE_URL_NO_SCHEME#*/}"
if [[ "$DATABASE_URL_NO_SCHEME" == "$DATABASE_URL_PATH_WITHOUT_QUERY" ]]; then
  DATABASE_URL_PATH_WITHOUT_QUERY=""
fi
DATABASE_URL_PATH_WITHOUT_QUERY="${DATABASE_URL_PATH_WITHOUT_QUERY%%\?*}"
DATABASE_URL_DB_NAME="${DATABASE_URL_PATH_WITHOUT_QUERY#/}"
if [[ -n "$DATABASE_URL_DB_NAME" ]]; then
  printf -v DATABASE_URL_DB_NAME '%b' "${DATABASE_URL_DB_NAME//%/\\x}"
fi

USES_BUNDLED_POSTGRES=0
if [[ "${DATABASE_URL_HOST,,}" == "postgres" ]]; then
  USES_BUNDLED_POSTGRES=1
elif [[ "$HAS_SOCKET_HOST_QUERY" -eq 1 && "${SOCKET_HOST_VALUE,,}" == "postgres" ]]; then
  USES_BUNDLED_POSTGRES=1
fi

POSTGRES_USER_EFFECTIVE="${POSTGRES_USER:-$BUNDLED_POSTGRES_DEFAULT_USER}"
POSTGRES_DB_EFFECTIVE="${POSTGRES_DB:-$BUNDLED_POSTGRES_DEFAULT_DB}"

if [[ "$USES_BUNDLED_POSTGRES" -eq 1 && -z "$DATABASE_URL_PASSWORD" ]]; then
  echo "DATABASE_URL targets the bundled postgres service but does not include a password. Set DATABASE_URL with the real POSTGRES_PASSWORD before running this deploy script." >&2
  exit 1
fi
if [[ "$USES_BUNDLED_POSTGRES" -eq 1 && -z "$DATABASE_URL_USERNAME" ]]; then
  echo "DATABASE_URL targets the bundled postgres service but does not include a username. Set DATABASE_URL to use POSTGRES_USER before running this deploy script." >&2
  exit 1
fi
if [[ "$USES_BUNDLED_POSTGRES" -eq 1 && "$DATABASE_URL_USERNAME" != "$POSTGRES_USER_EFFECTIVE" ]]; then
  echo "DATABASE_URL username does not match POSTGRES_USER for the bundled postgres service. Keep them in sync before running this deploy script." >&2
  exit 1
fi
if [[ "$USES_BUNDLED_POSTGRES" -eq 1 && -z "$DATABASE_URL_DB_NAME" ]]; then
  echo "DATABASE_URL targets the bundled postgres service but does not include a database name. Set DATABASE_URL to target POSTGRES_DB before running this deploy script." >&2
  exit 1
fi
if [[ "$USES_BUNDLED_POSTGRES" -eq 1 && "$DATABASE_URL_DB_NAME" != "$POSTGRES_DB_EFFECTIVE" ]]; then
  echo "DATABASE_URL database name does not match POSTGRES_DB for the bundled postgres service. Keep them in sync before running this deploy script." >&2
  exit 1
fi

POSTGRES_PASSWORD_NORMALIZED="${POSTGRES_PASSWORD,,}"
if [[ "$POSTGRES_PASSWORD_NORMALIZED" == "$BUNDLED_POSTGRES_DEFAULT_PASSWORD" ]] || placeholder_like_secret "$POSTGRES_PASSWORD"; then
  echo "POSTGRES_PASSWORD is still using an insecure default or placeholder. Set a real non-default password before running this deploy script." >&2
  exit 1
fi

if [[ "$USES_BUNDLED_POSTGRES" -eq 1 && -n "$DATABASE_URL_PASSWORD" && "$DATABASE_URL_PASSWORD_DECODED" != "$POSTGRES_PASSWORD" ]]; then
  echo "DATABASE_URL password does not match POSTGRES_PASSWORD for the bundled postgres service. Keep them in sync before running this deploy script." >&2
  exit 1
fi

BRIDGE_ENV="$ROOT/Sicret/bridge-bsc/bridge.env"
if [[ -f "$BRIDGE_ENV" ]]; then
  echo "Bridge runtime secrets remain sourced by docker-compose.prod.yml via service env_file: $BRIDGE_ENV"
fi

SKIP_PULL=0
SKIP_MIG=0
SKIP_POST_DEPLOY_CHECKS=0
WITH_ACP_NODE=0
for a in "$@"; do
  case "$a" in
    --skip-git-pull) SKIP_PULL=1 ;;
    --skip-migrations) SKIP_MIG=1 ;;
    --skip-post-deploy-checks) SKIP_POST_DEPLOY_CHECKS=1 ;;
    --with-acp-node|--full) WITH_ACP_NODE=1 ;;
  esac
done

if [[ "$SKIP_PULL" -eq 0 ]]; then
  git pull --ff-only
fi

export APP_BUILD_ID
APP_BUILD_ID="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo "APP_BUILD_ID=$APP_BUILD_ID (must match https://ancap.cloud/internal/frontend-build after deploy)"

echo "Validating docker-compose.prod.yml interpolation and required vars without printing resolved secrets..."
docker compose -f "$COMPOSE" config --quiet

# Default push/recover builds only api+frontend. Full/acp-node cargo rebuilds routinely
# overload the VPS (load 90+) and cancel mid-session — use --with-acp-node explicitly.
if [[ "$WITH_ACP_NODE" -eq 1 ]]; then
  echo "Building full compose stack (includes acp-node / Rust)..."
  docker compose -f "$COMPOSE" build
else
  echo "Building api + frontend only (pass --with-acp-node for Rust node rebuild)..."
  # Keep the wallet Rust compiler and Next.js build from competing for VPS RAM.
  docker compose -f "$COMPOSE" build api
  docker compose -f "$COMPOSE" build frontend
fi
if [[ "$SKIP_MIG" -eq 0 ]]; then
  # Apply additive schema changes from the new image before activating its API.
  # The previous API keeps serving until migration succeeds.
  docker compose -f "$COMPOSE" up -d --wait postgres redis
  docker compose -f "$COMPOSE" run --rm --no-deps api alembic upgrade head
fi

docker compose -f "$COMPOSE" up -d
# Bind-mounted nginx conf updates need a reload / recreate so acp1 + /rpc land.
docker compose -f "$COMPOSE" up -d --force-recreate proxy
docker compose -f "$COMPOSE" exec -T proxy nginx -t
docker compose -f "$COMPOSE" exec -T proxy nginx -s reload || true

if [[ -f "$ROOT/scripts/ensure-acp1-host-proxy.sh" ]]; then
  echo "Ensuring host nginx routes acp1.ancap.cloud → compose :8080 (Cloudflare Full SSL origin)..."
  sed -i 's/\r$//' "$ROOT/scripts/ensure-acp1-host-proxy.sh" 2>/dev/null || true
  bash "$ROOT/scripts/ensure-acp1-host-proxy.sh"
else
  echo "Skipping host acp1 proxy ensure (scripts/ensure-acp1-host-proxy.sh not present)."
fi

if [[ "$SKIP_POST_DEPLOY_CHECKS" -eq 1 ]]; then
  echo "Skipping live proxy/frontend verification by request (--skip-post-deploy-checks)."
  echo "Done. Build/start completed without live post-deploy verification."
  exit 0
fi

echo "Verifying live proxy liveness via /api/v1/system/health ..."
health_payload="$(wait_for_proxy_status "/api/v1/system/health" "ok" "Proxy liveness")"
echo "OK /api/v1/system/health -> status=$(python3 - <<'PY' "$health_payload"
import json, sys
print(json.loads(sys.argv[1]).get("status", ""))
PY
)"

echo "Verifying live proxy readiness via /api/v1/system/ready ..."
ready_payload="$(wait_for_proxy_status "/api/v1/system/ready" "ready" "Proxy readiness")"
echo "OK /api/v1/system/ready -> status=$(python3 - <<'PY' "$ready_payload"
import json, sys
print(json.loads(sys.argv[1]).get("status", ""))
PY
)"

echo "Verifying frontend build provenance via /internal/frontend-build ..."
build_payload="$(assert_frontend_build_id "$APP_BUILD_ID")"
echo "OK /internal/frontend-build -> NEXT_PUBLIC_APP_BUILD_ID=$(python3 - <<'PY' "$build_payload"
import json, sys
payload = json.loads(sys.argv[1])
print(payload.get("NEXT_PUBLIC_APP_BUILD_ID", ""))
PY
)"

if [[ "${ANCAP_SKIP_ACP1_DEPLOY_SMOKE:-}" == "1" ]]; then
  echo "Skipping acp1 RPC edge smoke (ANCAP_SKIP_ACP1_DEPLOY_SMOKE=1)."
else
echo "Verifying public ACP RPC host routing (compose Host + optional public edge)..."
acp1_local="$(curl -sS -m 15 -o /tmp/acp1_deploy_rpc.json -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -H 'Host: acp1.ancap.cloud' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getblockcount","params":[]}' \
  http://127.0.0.1:8080/rpc || true)"
echo "compose Host acp1 /rpc -> HTTP ${acp1_local} body=$(head -c 160 /tmp/acp1_deploy_rpc.json 2>/dev/null || true)"
if [[ "$acp1_local" != "200" ]]; then
  echo "compose acp1.ancap.cloud/rpc did not return 200 after deploy." >&2
  exit 1
fi
# Admin surface must fail closed without ACP_RPC_TOKEN (token never printed).
acp1_admin="$(curl -sS -m 15 -o /tmp/acp1_deploy_admin.json -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -H 'Host: acp1.ancap.cloud' \
  -d '{"jsonrpc":"2.0","id":1,"method":"stop","params":[]}' \
  http://127.0.0.1:8080/rpc || true)"
echo "compose Host acp1 admin deny -> HTTP ${acp1_admin} body=$(head -c 160 /tmp/acp1_deploy_admin.json 2>/dev/null || true)"
if grep -qiE 'ok|stopped|stopping' /tmp/acp1_deploy_admin.json 2>/dev/null; then
  echo "admin RPC appears open without token — fail closed." >&2
  exit 1
fi
acp1_public_code="$(curl -sS -m 20 -o /tmp/acp1_public_rpc.json -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getblockcount","params":[]}' \
  https://acp1.ancap.cloud/rpc || true)"
acp1_public_hdr="$(curl -sSI -m 20 https://acp1.ancap.cloud/healthz 2>/dev/null | tr -d '\r' || true)"
echo "public https://acp1.ancap.cloud/rpc -> HTTP ${acp1_public_code} body=$(head -c 160 /tmp/acp1_public_rpc.json 2>/dev/null || true)"
echo "public /healthz headers: $(echo "$acp1_public_hdr" | grep -iE 'HTTP/|x-ancap-upstream' | tr '\n' ' ')"
if [[ "$acp1_public_code" != "200" ]]; then
  echo "public acp1.ancap.cloud/rpc still not 200 — host/Cloudflare routing not fixed." >&2
  exit 1
fi
if ! echo "$acp1_public_hdr" | grep -qi 'x-ancap-upstream: *acp-rpc'; then
  echo "WARN: public /healthz missing X-Ancap-Upstream: acp-rpc (routing may still be wrong)" >&2
fi
fi

echo "Done. Open https://ancap.cloud/bridge/acp-bsc — if still 404, first confirm the verified build id at https://ancap.cloud/internal/frontend-build before blaming cache."
