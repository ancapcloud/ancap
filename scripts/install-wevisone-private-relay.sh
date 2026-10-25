#!/usr/bin/env bash
# Install a private TLS relay on the Docker host. No public listener is created.
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run as root'; exit 1; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIND_IP="$(docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')"
python3 - "$BIND_IP" <<'PY'
import ipaddress,sys
ip=ipaddress.ip_address(sys.argv[1])
assert any(ip in ipaddress.ip_network(cidr) for cidr in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16')), 'Relay must bind RFC1918 only'
PY
CERT_DIR=/etc/ancap-wevisone
install -d -m 700 "$CERT_DIR"
if [[ ! -f "$CERT_DIR/server.crt" ]]; then
  openssl req -x509 -newkey rsa:3072 -nodes -days 3650 \
    -subj /CN=ANCAP-private-OCR-CA -addext basicConstraints=critical,CA:TRUE \
    -addext keyUsage=critical,keyCertSign,cRLSign \
    -keyout "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" 2>/dev/null
  openssl req -new -newkey rsa:3072 -nodes -subj /CN=ANCAP-private-OCR \
    -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" 2>/dev/null
  printf 'subjectAltName=IP:%s\nbasicConstraints=critical,CA:FALSE\nextendedKeyUsage=serverAuth\nkeyUsage=critical,digitalSignature,keyEncipherment\n' "$BIND_IP" > "$CERT_DIR/server.ext"
  openssl x509 -req -in "$CERT_DIR/server.csr" -CA "$CERT_DIR/ca.crt" \
    -CAkey "$CERT_DIR/ca.key" -CAcreateserial -days 365 \
    -extfile "$CERT_DIR/server.ext" -out "$CERT_DIR/server.crt" 2>/dev/null
  chmod 600 "$CERT_DIR/ca.key" "$CERT_DIR/server.key"
fi
openssl x509 -in "$CERT_DIR/server.crt" -noout -checkend 604800
install -d -m 755 "$ROOT/Sicret/wevisone"
install -m 644 "$CERT_DIR/ca.crt" "$ROOT/Sicret/wevisone/ca.crt"
CONF="$CERT_DIR/relay.conf"
cat > "$CONF" <<EOF
server {
    listen $BIND_IP:18443 ssl;
    server_name _;
    ssl_certificate /etc/ocr/server.crt;
    ssl_certificate_key /etc/ocr/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    client_max_body_size 5m;
    access_log off;
    location = /v1/payment-ocr {
        proxy_pass http://127.0.0.1:18097;
        proxy_set_header Authorization \$http_authorization;
        proxy_read_timeout 65s;
        proxy_connect_timeout 5s;
    }
    location = /healthz {
        proxy_pass http://127.0.0.1:18097;
        proxy_read_timeout 5s;
    }
    location / { return 404; }
}
EOF
IMAGE=nginx:1.28-alpine
MOUNTS=(-v "$CONF:/etc/nginx/conf.d/default.conf:ro"
        -v "$CERT_DIR/server.crt:/etc/ocr/server.crt:ro"
        -v "$CERT_DIR/server.key:/etc/ocr/server.key:ro")
docker run --rm --network host "${MOUNTS[@]}" "$IMAGE" nginx -t
# Migrate only the earlier ANCAP OCR host-nginx config, if installed.
# Keep relay lifecycle independent of the website nginx/Docker startup ordering.
if [[ -f /etc/nginx/conf.d/ancap-wevisone-private.conf ]]; then
    rm -f /etc/nginx/conf.d/ancap-wevisone-private.conf
    nginx -t
    systemctl reload nginx
fi
if docker inspect ancap-wevisone-private-relay >/dev/null 2>&1; then
    docker restart ancap-wevisone-private-relay
else
    docker run -d --name ancap-wevisone-private-relay --restart unless-stopped \
        --network host "${MOUNTS[@]}" "$IMAGE"
fi
# A private-IP bind is still protected by the host firewall. Allow only the
# production Compose bridge and this one TLS destination; never a WAN source.
NETWORK=${WEVISONE_API_NETWORK:-current_default}
NET_ID=$(docker network inspect "$NETWORK" --format '{{.Id}}')
SUBNET=$(docker network inspect "$NETWORK" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
IFACE="br-${NET_ID:0:12}"
RULE=(-i "$IFACE" -s "$SUBNET" -d "$BIND_IP" -p tcp --dport 18443
      -m comment --comment ANCAP-private-OCR -j ACCEPT)
iptables -C INPUT "${RULE[@]}" 2>/dev/null || iptables -I INPUT 1 "${RULE[@]}"
printf 'Private OCR TLS relay ready: https://%s:18443 (SSH upstream 127.0.0.1:18097)\n' "$BIND_IP"
