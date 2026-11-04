"""Regression guard: every state-changing API route must require an identity.

Background (2026-11-04 audit): several legacy core-engine routes (contract lifecycle,
risk kill switch, dispute verdicts, scenario runner, strategy versions, listings) were
reachable without authentication or ownership checks. This test walks the FastAPI
dependency tree of every POST/PUT/PATCH/DELETE route and fails when a new route is added
without an auth dependency or an explicit, reviewed entry in ``PUBLIC_MUTATING_ROUTES``.

To add a genuinely public route (quotes, login, webhooks with their own signature check),
add it to the allowlist below together with a one-line reason.
"""
from __future__ import annotations

from fastapi.routing import APIRoute

from app.main import app

# Dependencies that establish caller identity (user, agent key, operator or cron secret).
AUTH_DEPENDENCY_NAMES = {
    "require_auth",
    "require_platform_admin",
    "require_admin",
    "get_current_user_id",
    "require_agent_id",
    "get_agent_id_from_api_key",
}

# Reviewed public mutating routes: path -> reason.
PUBLIC_MUTATING_ROUTES: dict[str, str] = {
    "/v1/auth/login": "credential exchange",
    "/v1/auth/users": "registration",
    "/v1/auth/password/forgot": "password reset request (rate limited)",
    "/v1/auth/password/reset": "token-bound password reset",
    "/v1/auth/password/recover-with-wallet": "wallet-signature recovery",
    "/v1/auth/wallet/nonce": "wallet login challenge",
    "/v1/auth/wallet/verify": "wallet signature verification",
    "/v1/onboarding/challenge": "agent onboarding challenge",
    "/v1/onboarding/attest": "challenge-bound attestation",
    "/v1/webhooks/stripe": "Stripe signature verified in handler",
    "/v1/system/jobs/tick": "X-Cron-Secret enforced in handler",
    "/v1/system/jobs/tick/async": "X-Cron-Secret enforced in handler",
    "/v1/mcp": "MCP session teardown; session-id bound",
    "/v1/home-chat/messages": "public landing chat (rate limited)",
    "/v1/commerce/ramp-waitlist": "public waitlist signup",
    "/v1/token-snapshot": "read-only token check (rate limited)",
    "/v1/acp/tx/estimate-fee": "read-only quote",
    "/v1/assay/gc/analyze": "stateless analysis",
    "/v1/bridge/quote/bsc-to-acp": "read-only quote",
    "/v1/field-services/quote": "read-only quote",
    "/v1/insurance/quote": "read-only quote",
    "/v1/starlink-install/quote": "read-only quote",
    "/v1/mobile/exchange/quote": "read-only quote",
    "/v1/mobile/numismatic/authenticate": "stateless analysis",
    "/v1/mobile/numismatic/value": "stateless analysis",
    "/v1/mobile/smart-pay/parse": "stateless parse",
    "/v1/mobile/smart-pay/quote": "read-only quote",
    "/v1/sacp/intents/mint": "intent only; awaits on-chain collateral",
    "/v1/sacp/intents/redeem": "intent only; awaits on-chain burn",
    "/v1/wallet/acp/swap/quote": "read-only quote",
    "/v1/wallet/acp/otc/quote/commodity": "read-only quote",
    "/v1/wallet/acp/otc/quote/goods": "read-only quote",
    "/v1/wallet/acp/otc/quote/ip": "read-only quote",
    "/v1/wallet/acp/otc/quote/metal": "read-only quote",
    "/v1/wallet/acp/otc/quote/real-estate": "read-only quote",
    "/v1/wallet/acp/otc/quote/space": "read-only quote",
}

_IDENTITY_HINTS = ("auth", "admin", "secret", "operator", "cron", "owner", "signature", "api_key", "principal")
_IDENTITY_HEADERS = ("secret", "key", "authorization", "signature", "token")


def _dependency_names(dependant, acc: set[str]) -> set[str]:
    for sub in dependant.dependencies:
        acc.add(getattr(sub.call, "__name__", str(sub.call)))
        _dependency_names(sub, acc)
    return acc


def _has_identity(route: APIRoute) -> bool:
    names = _dependency_names(route.dependant, set())
    if names & AUTH_DEPENDENCY_NAMES:
        return True
    if any(h in n.lower() for n in names for h in _IDENTITY_HINTS):
        return True
    headers = " ".join(p.name.lower() for p in route.dependant.header_params)
    return any(h in headers for h in _IDENTITY_HEADERS)


def _unguarded_mutating_routes() -> list[str]:
    missing: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not (route.methods - {"GET", "HEAD", "OPTIONS"}):
            continue
        if route.path in PUBLIC_MUTATING_ROUTES or not route.path.startswith("/v1/"):
            continue
        if not _has_identity(route):
            missing.append(f"{sorted(route.methods)} {route.path} ({route.endpoint.__module__})")
    return sorted(missing)


def test_every_mutating_route_requires_identity_or_is_reviewed_public():
    missing = _unguarded_mutating_routes()
    assert not missing, (
        "State-changing routes without an auth dependency. Add require_auth / "
        "require_platform_admin (plus an ownership check), or list the route in "
        "PUBLIC_MUTATING_ROUTES with a reason:\n" + "\n".join(missing)
    )


def test_previously_open_routes_are_now_guarded():
    guarded = {
        "/v1/contracts/{contract_id}/complete",
        "/v1/contracts/{contract_id}/accept",
        "/v1/contracts/{contract_id}/cancel",
        "/v1/risk/kill",
        "/v1/risk/limits",
        "/v1/disputes/{dispute_id}/verdict",
        "/v1/flows/run",
        "/v1/strategies/{strategy_id}/versions",
        "/v1/listings",
        "/v1/funds/{fund_id}/allocate",
        "/v1/verticals/{vertical_id}/review",
        "/v1/reviews/ai",
    }
    by_path = {r.path: r for r in app.routes if isinstance(r, APIRoute) and r.methods - {"GET", "HEAD"}}
    for path in guarded:
        assert path in by_path, path
        assert _has_identity(by_path[path]), path
