#!/usr/bin/env python3
"""Log indicative swap sizes vs thin-pool spot (GeckoTerminal), not treasury cycles."""

from __future__ import annotations

import argparse
import json
import urllib.request

GT_POOL = "0xf391ca2bcbab93afa23326ebf1e35db950841601"
GT_URL = f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/{GT_POOL}"


def _spot_usd() -> float | None:
    req = urllib.request.Request(GT_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    attrs = (data.get("data") or {}).get("attributes") or {}
    raw = attrs.get("base_token_price_usd")
    return float(raw) if raw else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd-sizes", default="100,250,500", help="Comma-separated USD notionals")
    args = parser.parse_args()

    spot = _spot_usd()
    sizes = [float(x.strip()) for x in args.usd_sizes.split(",") if x.strip()]
    rows = []
    for usd in sizes:
        wacp = (usd / spot) if spot and spot > 0 else None
        rows.append({"usd_in": usd, "indicative_wacp_at_spot": wacp, "note": "Use PancakeSwap UI for executable quote"})

    print(
        json.dumps(
            {
                "ok": spot is not None,
                "reference_pool_v2": GT_POOL,
                "spot_usd_per_wacp": spot,
                "rows": rows,
            },
            indent=2,
        )
    )
    return 0 if spot else 1


if __name__ == "__main__":
    raise SystemExit(main())
