"""Webhook destination URL policy (SSRF hardening)."""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from app.config import get_settings

DNS_LOOKUP_TIMEOUT_S = 3.0


class UnsafeWebhookUrl(ValueError):
    """Raised when a webhook URL is not allowed as a server-side fetch target."""


@dataclass(frozen=True)
class ValidatedWebhookTarget:
    """A webhook URL that passed policy checks, optionally DNS-pinned."""

    url: str
    scheme: str
    hostname: str
    port: int
    path: str
    pinned_ip: str | None

    def pinned_request_url(self) -> str:
        """URL that connects to the validated IP (Host/SNI still use hostname)."""
        if not self.pinned_ip:
            return self.url
        host = self.pinned_ip
        try:
            ip_obj = ipaddress.ip_address(host)
            if isinstance(ip_obj, ipaddress.IPv6Address):
                host = f"[{host}]"
        except ValueError:
            # A DNS hostname is valid here; only literal IPv6 addresses need brackets.
            pass
        netloc = f"{host}:{self.port}"
        parsed = urlparse(self.url)
        return urlunparse((self.scheme, netloc, parsed.path or "/", parsed.params, parsed.query, ""))


_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata",
    }
)


def _canonical_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Unwrap IPv4-mapped IPv6 so CGNAT/private checks apply to the embedded v4."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    ip = _canonical_ip(ip)
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True
    # Cloud metadata / CGNAT / IPv6 ULA & link-local (belt-and-suspenders)
    blocked_nets = (
        "169.254.0.0/16",
        "100.64.0.0/10",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
    return any(ip in ipaddress.ip_network(net) for net in blocked_nets)


def _resolve_public_ip(host: str, port: int) -> str:
    """Resolve host and return the first public IP; raise if any answer is blocked."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeWebhookUrl("URL host could not be resolved") from exc
    if not infos:
        raise UnsafeWebhookUrl("URL host could not be resolved")

    public_ips: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        try:
            resolved = ipaddress.ip_address(sockaddr[0])
        except ValueError:
            continue
        if _is_blocked_ip(resolved):
            raise UnsafeWebhookUrl("URL resolves to a blocked address")
        public_ips.append(str(_canonical_ip(resolved)))
    if not public_ips:
        raise UnsafeWebhookUrl("URL host could not be resolved")
    return public_ips[0]


def validate_webhook_url(url: str, *, resolve_dns: bool = True) -> ValidatedWebhookTarget:
    """Validate webhook URL for SSRF safety.

    When resolve_dns=True, also resolves DNS once and returns a pinned IP so the
    HTTP client can connect without a second (rebinding-prone) lookup.
    """
    raw = (url or "").strip()
    if not raw or len(raw) > 2048:
        raise UnsafeWebhookUrl("URL is empty or too long")

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    settings = get_settings()
    env = (settings.environment or "development").strip().lower()
    if env == "production":
        if scheme != "https":
            raise UnsafeWebhookUrl("Production webhooks require https")
    elif scheme not in {"http", "https"}:
        raise UnsafeWebhookUrl("URL must be http or https")

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        raise UnsafeWebhookUrl("URL host is required")
    if host in _BLOCKED_HOSTNAMES or host.endswith(".local") or host.endswith(".internal"):
        raise UnsafeWebhookUrl("URL host is not allowed")
    if parsed.username or parsed.password:
        raise UnsafeWebhookUrl("URL must not include credentials")

    default_port = 443 if scheme == "https" else 80
    port = int(parsed.port or default_port)
    if port in {22, 25, 465, 587, 3306, 5432, 6379, 11211, 27017}:
        raise UnsafeWebhookUrl("URL port is not allowed")

    pinned_ip: str | None = None
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None
    if literal_ip is not None:
        if _is_blocked_ip(literal_ip):
            raise UnsafeWebhookUrl("URL resolves to a blocked address")
        pinned_ip = str(_canonical_ip(literal_ip))
    elif resolve_dns:
        pinned_ip = _resolve_public_ip(host, port)

    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    return ValidatedWebhookTarget(
        url=raw,
        scheme=scheme,
        hostname=host,
        port=port,
        path=path,
        pinned_ip=pinned_ip,
    )


async def validate_webhook_url_async(url: str, *, resolve_dns: bool = True) -> ValidatedWebhookTarget:
    """Async wrapper: DNS / socket work runs in a worker thread with a hard timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(validate_webhook_url, url, resolve_dns=resolve_dns),
            timeout=DNS_LOOKUP_TIMEOUT_S + 1.0,
        )
    except TimeoutError as exc:
        raise UnsafeWebhookUrl("URL host lookup timed out") from exc
