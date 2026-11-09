#!/usr/bin/env bash
# Ensure public https://acp1.ancap.cloud/rpc reaches compose nginx (:8080).
#
# Root cause history:
# - Cloudflare Full SSL hits Hestia on 185.x:443 (not *:443 / not loopback).
# - Hestia had `location = /rpc { proxy_pass http://IP:18080/... }` (dead port) → HTML 404.
# - A catch-all `listen 80` drop-in never binds beside Hestia's IP-specific listeners.
#
# Strategy: rewrite Hestia domain vhosts in place (exact /rpc + /healthz + / → :8080).
# Idempotent — safe on every deploy. Do NOT call v-rebuild-web-domains after patching.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="acp1.ancap.cloud"
MARKER="ANCAP_ACP1_HOST_PROXY"
PUB_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [[ -z "${PUB_IP}" ]]; then
  PUB_IP="127.0.0.1"
fi

if [[ "${1:-}" != "--smoke-only" && "$(id -u)" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    sudo bash "$0" "$@"
    exit $?
  fi
  echo "need root to patch host nginx for ${DOMAIN}" >&2
  exit 1
fi

patch_vhosts() {
  python3 - <<'PY'
from pathlib import Path
import re

files = []
for p in [
    Path("/etc/nginx/conf.d/domains/acp1.ancap.cloud.conf"),
    Path("/etc/nginx/conf.d/domains/acp1.ancap.cloud.ssl.conf"),
    Path("/home/admin/conf/web/acp1.ancap.cloud/nginx.conf"),
    Path("/home/admin/conf/web/acp1.ancap.cloud/nginx.ssl.conf"),
]:
    if p.exists():
        files.append(p)

if not files:
    print("skip: no Hestia/domain acp1 nginx confs found (not the production VPS?)")
    raise SystemExit(0)

block = """
    # ANCAP_ACP1_HOST_PROXY: /rpc + /healthz → compose nginx :8080
    location = /rpc {
        proxy_pass http://127.0.0.1:8080/rpc;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }
    location = /rpc/ {
        return 308 /rpc;
    }
    location = /healthz {
        proxy_pass http://127.0.0.1:8080/healthz;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
"""

for path in files:
    text = path.read_text(encoding="utf-8")
    # Backup once.
    bak = path.with_suffix(path.suffix + ".bak-ancap")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")

    # Strip prior ANCAP location clusters and any exact /rpc|/healthz|location /.
    while "ANCAP_ACP1_HOST_PROXY" in text:
        nxt = re.sub(
            r"\n[ \t]*#[^\n]*ANCAP_ACP1_HOST_PROXY[^\n]*(?:\n[ \t]*location[^\n]*\{[^{}]*\})+",
            "\n",
            text,
            count=1,
            flags=re.S,
        )
        if nxt == text:
            # Orphan marker comments
            text = text.replace("ANCAP_ACP1_HOST_PROXY", "ANCAP_ACP1_HOST_PROXY_OLD")
            break
        text = nxt

    text = re.sub(r"\n[ \t]*location\s*=\s*/rpc\s*\{[^{}]*\}", "", text, flags=re.S)
    text = re.sub(r"\n[ \t]*location\s*=\s*/rpc/\s*\{[^{}]*\}", "", text, flags=re.S)
    text = re.sub(r"\n[ \t]*location\s*=\s*/healthz\s*\{[^{}]*\}", "", text, flags=re.S)
    # Remove generic location / (docroot or stale proxy). Keep ACME ^~ and regex denies.
    text = re.sub(r"\n[ \t]*location\s*/\s*\{[^{}]*\}", "", text, flags=re.S)
    # Kill legacy dead upstream if still present elsewhere.
    text = re.sub(
        r"proxy_pass\s+http://[\d.]+:18080[^;]*;",
        "proxy_pass http://127.0.0.1:8080/rpc;",
        text,
    )

    text = re.sub(r"\}\s*$", block + "\n}\n", text, count=1)
    path.write_text(text, encoding="utf-8")
    print(f"patched {path}")
PY
}

remove_conflicting_dropin() {
  # Catch-all *:80/:443 drop-ins cannot bind beside Hestia IP listeners and
  # only produce conflicting server_name warnings. Prefer in-place domain patches.
  local drop
  for drop in \
    /etc/nginx/conf.d/acp1-ancap-cloud-compose-proxy.conf \
    /etc/nginx/conf.d/zz-acp1-ancap-cloud.conf
  do
    if [[ -f "$drop" ]]; then
      mv -f "$drop" "${drop}.disabled-ancap" 2>/dev/null || rm -f "$drop"
      echo "disabled conflicting drop-in $drop"
    fi
  done
}

reload_nginx() {
  nginx -t
  if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet nginx; then
    systemctl reload nginx
  else
    nginx -s reload || true
  fi
  echo "nginx reloaded"
}

if [[ "${1:-}" != "--smoke-only" ]]; then
if [[ ! -d /etc/nginx/conf.d ]]; then
  echo "No /etc/nginx/conf.d — skipping (not the VPS host?)"
  exit 0
fi

acp1_vhost_present=0
for candidate in \
  /etc/nginx/conf.d/domains/acp1.ancap.cloud.conf \
  /etc/nginx/conf.d/domains/acp1.ancap.cloud.ssl.conf \
  /home/admin/conf/web/acp1.ancap.cloud/nginx.conf \
  /home/admin/conf/web/acp1.ancap.cloud/nginx.ssl.conf
do
  if [[ -f "$candidate" ]]; then
    acp1_vhost_present=1
    break
  fi
done

if [[ "$acp1_vhost_present" -eq 0 ]]; then
  echo "No acp1.ancap.cloud Hestia vhost on this host — skipping host nginx patch/smoke."
  exit 0
fi

remove_conflicting_dropin
patch_vhosts
reload_nginx
fi

# Reload is asynchronous: old workers can briefly serve the previous vhost.
# --smoke-only also permits a rootless route diagnostic without changing nginx.
attempts="${ACP1_SMOKE_ATTEMPTS:-10}"
delay="${ACP1_SMOKE_DELAY:-2}"
if [[ ! "$attempts" =~ ^[0-9]+$ || "$attempts" -lt 1 || "$attempts" -gt 30 || ! "$delay" =~ ^[0-9]+$ || "$delay" -gt 10 ]]; then
  echo "Invalid ACP1 smoke retry settings" >&2
  exit 1
fi
smoke_dir="$(mktemp -d /tmp/ancap-acp1-smoke.XXXXXXXX)"
trap 'rm -f "$smoke_dir/compose.json" "$smoke_dir/host.json"; rmdir "$smoke_dir"' EXIT

probe_rpc() {
  local label="$1" output="$2" url="$3"
  shift 3
  local code
  code="$(curl -skS --noproxy '*' -m 10 -o "$output" -w '%{http_code}' \
    -H 'Content-Type: application/json' -H "Host: ${DOMAIN}" \
    --data-binary '{"jsonrpc":"2.0","id":1,"method":"getblockcount","params":[]}' \
    "$@" "$url" || true)"
  echo "$label: HTTP ${code}"
  [[ "$code" == "200" ]] || return 1
  python3 - "$output" <<'PY'
import json
import sys
try:
    with open(sys.argv[1], encoding="utf-8") as stream:
        data = json.load(stream)
    ok = (isinstance(data, dict) and data.get("jsonrpc") == "2.0"
          and type(data.get("id")) is int and data["id"] == 1
          and "error" not in data and type(data.get("result")) is int
          and data["result"] >= 0)
except (OSError, ValueError):
    ok = False
raise SystemExit(0 if ok else 1)
PY
}

for ((attempt=1; attempt<=attempts; attempt++)); do
  echo "== RPC routing smoke attempt ${attempt}/${attempts}"
  # Require both the actual upstream and the TLS origin used by Cloudflare.
  # --resolve preserves domain SNI; a Host header on an IP URL alone does not.
  compose_ok=0
  host_ok=0
  if probe_rpc 'compose :8080' "$smoke_dir/compose.json" 'http://127.0.0.1:8080/rpc'; then compose_ok=1; fi
  if probe_rpc 'host :443' "$smoke_dir/host.json" "https://${DOMAIN}/rpc" \
    --resolve "${DOMAIN}:443:${PUB_IP}"; then host_ok=1; fi
  if [[ "$compose_ok" == 1 && "$host_ok" == 1 ]]; then
    echo "OK compose and host TLS origin return valid getblockcount"
    exit 0
  fi
  if ((attempt < attempts)); then sleep "$delay"; fi
done

echo "ACP1 RPC routing did not become ready within the bounded retry window" >&2
ss -lntp 2>/dev/null | grep -E ':80 |:443 ' || true
exit 1
