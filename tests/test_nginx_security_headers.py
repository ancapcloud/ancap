from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NGINX_CONF = REPO_ROOT / "infra" / "nginx" / "default.conf"

EXPECTED_PROXY_HIDE_HEADERS = [
    "proxy_hide_header X-Frame-Options;",
    "proxy_hide_header X-Content-Type-Options;",
    "proxy_hide_header Referrer-Policy;",
    "proxy_hide_header Permissions-Policy;",
    "proxy_hide_header Strict-Transport-Security;",
]

PROXIED_LOCATION_SNIPPETS = [
    """location / {\n        proxy_pass http://ancap_api;""",
    """location = /rpc {\n        limit_req zone=acp_rpc burst=20 nodelay;\n        proxy_pass http://acp-node:8545/rpc;""",
    """location = /openapi.json {\n        proxy_pass http://ancap_api/openapi.json;""",
    """location = /docs {\n        proxy_pass http://ancap_api/docs;""",
    """location = /docs/ {\n        proxy_pass http://ancap_api/docs/;""",
    """location = /redoc {\n        proxy_pass http://ancap_api/redoc;""",
    """location = /redoc/ {\n        proxy_pass http://ancap_api/redoc/;""",
    """location ^~ /api/v1/mcp {\n        proxy_pass http://ancap_api/v1/mcp;""",
    """location ^~ /api/ {\n        proxy_pass http://ancap_api/;""",
    """location = /api {\n        proxy_pass http://ancap_api/;""",
    """location ^~ /v1/mcp {\n        proxy_pass http://ancap_api;""",
    """location ^~ /v1/ {\n        proxy_pass http://ancap_api;""",
    """location ^~ /_next/ {\n        proxy_pass http://ancap_frontend;""",
    """location / {\n        proxy_pass http://ancap_frontend;""",
]


def _read_nginx_conf() -> str:
    return NGINX_CONF.read_text(encoding="utf-8")


def test_named_upstreams_are_defined():
    config = _read_nginx_conf()
    assert "upstream ancap_api {" in config
    assert "server api:8000;" in config
    assert "upstream ancap_frontend {" in config
    assert "server frontend:3000;" in config
    # Variable-based proxy_pass historically mis-routed /api onto Next.js.
    assert "set $upstream_api" not in config
    assert "set $upstream_frontend" not in config


def test_proxied_locations_hide_upstream_security_headers_before_readding_them():
    config = _read_nginx_conf()

    for snippet in PROXIED_LOCATION_SNIPPETS:
        assert snippet in config, f"expected nginx location block missing from {NGINX_CONF}"
        block = config.split(snippet, 1)[1].split("\n    }", 1)[0]
        for header in EXPECTED_PROXY_HIDE_HEADERS:
            assert header in block, f"missing `{header}` in proxied nginx location starting with: {snippet!r}"


def test_proxied_locations_readd_single_source_of_truth_security_headers():
    config = _read_nginx_conf()

    expected_add_headers = [
        "add_header X-Frame-Options DENY always;",
        "add_header X-Content-Type-Options nosniff always;",
        "add_header Referrer-Policy strict-origin-when-cross-origin always;",
        'add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;',
        'add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;',
    ]

    for snippet in PROXIED_LOCATION_SNIPPETS:
        block = config.split(snippet, 1)[1].split("\n    }", 1)[0]
        for header in expected_add_headers:
            assert header in block, f"missing `{header}` in proxied nginx location starting with: {snippet!r}"


def test_api_locations_mark_upstream_for_debug():
    config = _read_nginx_conf()
    assert "add_header X-Ancap-Upstream api always;" in config
    assert "add_header X-Ancap-Upstream frontend always;" in config
    assert "add_header X-Ancap-Upstream acp-rpc always;" in config


def test_acp1_rpc_host_and_ancap_fallback_are_wired():
    config = _read_nginx_conf()
    assert "server_name acp1.ancap.cloud;" in config
    assert "location = /healthz {" in config
    assert '"service":"acp-rpc"' in config or '"service": "acp-rpc"' in config
    # Main site exposes the same RPC upstream when Host is ancap.cloud.
    assert config.count("proxy_pass http://acp-node:8545/rpc;") >= 2
