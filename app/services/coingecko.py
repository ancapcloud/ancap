"""CoinGecko market-data client (indicative quotes only).

API key must come from env (`COINGECKO_API_KEY`) — never commit secrets.
Demo keys use header `x-cg-demo-api-key` against api.coingecko.com.
"""

from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.config import get_settings

_CACHE: dict[str, Any] = {"at": 0.0, "payload": None}
_GT_CACHE: dict[str, Any] = {"at": 0.0, "price": None}
# Top majors by market presence (indicative CoinGecko spot, not settlement).
_DEFAULT_IDS = ("bitcoin", "ethereum", "tether", "binancecoin", "solana")
_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "tether": "USDT",
    "binancecoin": "BNB",
    "solana": "SOL",
}
# Official wACP on BSC + canonical PancakeSwap V2 pool (GeckoTerminal).
_WACP_BSC = "0x349797e2f1a4fd722af2db181ab1c4ed7606f402"
_OFFICIAL_POOL = "0xf391ca2bcbab93afa23326ebf1e35db950841601"


def _api_key() -> str:
    return (get_settings().coingecko_api_key or "").strip()


def is_configured() -> bool:
    settings = get_settings()
    return bool(getattr(settings, "coingecko_enabled", True)) and bool(_api_key())


def _headers() -> dict[str, str]:
    key = _api_key()
    # Demo plan keys (CG-…) use the demo header; Pro keys use pro header + pro host.
    if key.upper().startswith("CG-"):
        return {"x-cg-demo-api-key": key, "accept": "application/json"}
    return {"x-cg-pro-api-key": key, "accept": "application/json"}


def _base_url() -> str:
    settings = get_settings()
    configured = (getattr(settings, "coingecko_base_url", None) or "").strip()
    if configured:
        return configured.rstrip("/")
    key = _api_key()
    if key and not key.upper().startswith("CG-"):
        return "https://pro-api.coingecko.com/api/v3"
    return "https://api.coingecko.com/api/v3"


def _ttl() -> int:
    return int(getattr(get_settings(), "coingecko_cache_ttl_seconds", 60) or 60)


def _to_dec(raw: Any) -> Decimal | None:
    try:
        if raw is None:
            return None
        return Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        return None


async def fetch_simple_prices(*, ids: tuple[str, ...] | list[str] | None = None, vs: str = "usd") -> dict[str, Any]:
    """Return cached CoinGecko simple/price payload + normalized rows."""
    settings = get_settings()
    if not bool(getattr(settings, "coingecko_enabled", True)):
        return {
            "configured": False,
            "enabled": False,
            "provider": "coingecko",
            "status": "disabled",
            "prices": [],
            "notes": ["CoinGecko integration is disabled (COINGECKO_ENABLED=false)."],
        }
    if not _api_key():
        return {
            "configured": False,
            "enabled": True,
            "provider": "coingecko",
            "status": "not_configured",
            "prices": [],
            "notes": ["Set COINGECKO_API_KEY in the environment to enable live market data."],
        }

    coin_ids = tuple(ids or _DEFAULT_IDS)
    cache_key = f"{','.join(coin_ids)}|{vs}"
    now = time.time()
    cached = _CACHE.get("payload")
    if cached and cached.get("cache_key") == cache_key and now - float(_CACHE.get("at") or 0) < _ttl():
        return cached

    url = f"{_base_url()}/simple/price"
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": vs,
        "include_last_updated_at": "true",
    }
    notes: list[str] = [
        "Indicative third-party market data from CoinGecko. Not a settlement price and not investment advice.",
        "See /legal/market-data for disclosure.",
    ]
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params, headers=_headers())
        if resp.status_code >= 400:
            return {
                "configured": True,
                "enabled": True,
                "provider": "coingecko",
                "status": "error",
                "http_status": resp.status_code,
                "prices": [],
                "notes": notes + [f"CoinGecko HTTP {resp.status_code}"],
            }
        raw = resp.json()
    except Exception as exc:  # noqa: BLE001 — surface soft failure to UI
        return {
            "configured": True,
            "enabled": True,
            "provider": "coingecko",
            "status": "error",
            "prices": [],
            "notes": notes + [f"CoinGecko request failed: {type(exc).__name__}"],
        }

    rows: list[dict[str, Any]] = []
    for coin_id in coin_ids:
        block = raw.get(coin_id) or {}
        price = _to_dec(block.get(vs))
        rows.append(
            {
                "id": coin_id,
                "symbol": _SYMBOLS.get(coin_id, coin_id.upper()),
                "vs_currency": vs.upper(),
                "price": str(price) if price is not None else None,
                "last_updated_at": block.get("last_updated_at"),
            }
        )

    payload = {
        "configured": True,
        "enabled": True,
        "provider": "coingecko",
        "status": "ok",
        "vs_currency": vs.upper(),
        "cache_ttl_seconds": _ttl(),
        "cache_key": cache_key,
        "prices": rows,
        "notes": notes,
        "attribution": "Market data provided by CoinGecko (https://www.coingecko.com).",
    }
    _CACHE["at"] = now
    _CACHE["payload"] = payload
    return payload


async def usdt_usd_price() -> Decimal | None:
    data = await fetch_simple_prices(ids=("tether",), vs="usd")
    for row in data.get("prices") or []:
        if row.get("id") == "tether" and row.get("price"):
            return Decimal(str(row["price"]))
    return None


async def fetch_wacp_usd_geckoterminal() -> Decimal | None:
    """DEX spot for official wACP/USDT pool on GeckoTerminal. Not legal settlement advice."""
    from app.services import market_economy as me

    spot, _source = await me.get_wacp_usd_oracle()
    now = time.time()
    _GT_CACHE["at"] = now
    _GT_CACHE["price"] = format(spot, "f")
    return spot


async def fetch_wacp_usd_coingecko() -> Decimal | None:
    """Once CoinGecko assigns a coin id, prefer that simple/price feed."""
    settings = get_settings()
    coin_id = (getattr(settings, "coingecko_wacp_coin_id", None) or "").strip()
    if not coin_id or not is_configured():
        return None
    data = await fetch_simple_prices(ids=(coin_id,), vs="usd")
    for row in data.get("prices") or []:
        if row.get("id") == coin_id and row.get("price"):
            return _to_dec(row.get("price"))
    return None


def platform_indicative_rows(
    *,
    vs: str = "usd",
    usdt_usd: Decimal | None = None,
    wacp_usd: Decimal | None = None,
) -> list[dict[str, Any]]:
    """ACP / wACP / sACP indicative USD context (not settlement).

    When a live/oracle wACP spot exists, ACP USD = 10 × wACP (bridge 1 ACP ↔ 10 wACP).
    """
    if (vs or "usd").lower() != "usd":
        return []
    from app.services import market_economy as me
    from app.services.bridge_decimal import WACP_PER_ACP, acp_usd_from_wacp_usd

    settings = get_settings()
    acp_per_usdt = me.usdt_to_acp_desk_rate(wacp_usd=wacp_usd)
    if acp_per_usdt <= 0:
        acp_per_usdt = Decimal("1")
    usdt = usdt_usd if usdt_usd is not None else Decimal("1")
    desk_acp_usd = (usdt / acp_per_usdt).quantize(Decimal("0.00000001"))
    wacp_price = wacp_usd if wacp_usd is not None and wacp_usd > 0 else (
        desk_acp_usd / Decimal(WACP_PER_ACP)
    )
    # Bridge doctrine: 1 ACP ↔ 10 wACP.
    acp_usd = (
        acp_usd_from_wacp_usd(wacp_price)
        if wacp_usd is not None and wacp_usd > 0
        else desk_acp_usd
    )
    _ = settings  # reserved for future desk flags
    vs_u = "USD"
    return [
        {"id": "acp", "symbol": "ACP", "vs_currency": vs_u, "price": format(acp_usd, "f"), "last_updated_at": None},
        {"id": "wacp", "symbol": "wACP", "vs_currency": vs_u, "price": format(wacp_price, "f"), "last_updated_at": None},
        {"id": "sacp", "symbol": "sACP", "vs_currency": vs_u, "price": "1", "last_updated_at": None},
    ]


async def fetch_market_board(*, vs: str = "usd") -> dict[str, Any]:
    """Home/ticker board: platform ACP rails first, then CoinGecko majors."""
    vs_n = (vs or "usd").lower().strip() or "usd"
    cg = await fetch_simple_prices(vs=vs_n)
    usdt: Decimal | None = None
    for row in cg.get("prices") or []:
        if row.get("id") == "tether" and row.get("price"):
            usdt = _to_dec(row.get("price"))
            break
    wacp_usd = await fetch_wacp_usd_coingecko()
    wacp_source = "coingecko"
    if wacp_usd is None:
        wacp_usd = await fetch_wacp_usd_geckoterminal()
        wacp_source = "geckoterminal" if wacp_usd is not None else "desk"
    platform = platform_indicative_rows(vs=vs_n, usdt_usd=usdt, wacp_usd=wacp_usd)
    prices = platform + list(cg.get("prices") or [])
    status = str(cg.get("status") or "error")
    if platform and status != "ok":
        status = "partial"
    notes = list(cg.get("notes") or [])
    notes = [
        "ACP USD ≈ 10 × official wACP DEX spot (bridge 1 ACP ↔ 10 wACP) when oracle is live; "
        "USDT→ACP desk uses 1/(10×wacp_usd). sACP soft-peg target ≈ 1 USD. Indicative only — not investment advice.",
        f"wACP spot source: {wacp_source}. Official pool: {_OFFICIAL_POOL}. "
        "See docs/MARKET_ALIGNED_ECONOMY.md and /legal/market-data.",
        *notes,
    ]
    attribution = cg.get("attribution")
    if wacp_source == "geckoterminal":
        attribution = (
            (attribution + " ") if attribution else ""
        ) + "wACP DEX spot via GeckoTerminal (CoinGecko). See /legal/market-data."
    return {
        **cg,
        "status": status,
        "prices": prices,
        "notes": notes,
        "attribution": attribution
        or "Platform ACP rails + CoinGecko spot context. See /legal/market-data.",
    }


def clear_cache() -> None:
    _CACHE["at"] = 0.0
    _CACHE["payload"] = None
    _GT_CACHE["at"] = 0.0
    _GT_CACHE["price"] = None
