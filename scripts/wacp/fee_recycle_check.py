#!/usr/bin/env python3
"""Operator go/no-go: platform fee revenue vs V3 recycle threshold.

Usage (from repo root):

  python scripts/wacp/fee_recycle_check.py
  python scripts/wacp/fee_recycle_check.py --base-url https://api.ancap.cloud/v1

Does not move funds. After eligible=true, human-sign wrap + Add Liquidity on V3.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.market_economy import OFFICIAL_WACP_POOL_V3  # noqa: E402
from app.services.wacp_fee_recycle import _to_dec, _revenue_from_status  # noqa: E402

DEFAULT_MIN = Decimal("50")
DEFAULT_POOL = OFFICIAL_WACP_POOL_V3


def _fetch_treasury(base_url: str) -> dict:
    url = base_url.rstrip("/") + "/treasury/status"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ancap-wacp-fee-recycle/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://api.ancap.cloud/v1")
    parser.add_argument(
        "--min-revenue-acp",
        type=str,
        default=str(DEFAULT_MIN),
        help="Minimum ledger revenue_30d ACP (positive finite threshold)",
    )
    parser.add_argument("--v3-pool", default=DEFAULT_POOL)
    args = parser.parse_args()

    try:
        min_rev = _to_dec(args.min_revenue_acp)
        if min_rev <= 0:
            raise ValueError("Threshold must be positive")
        status = _fetch_treasury(args.base_url)
        revenue = _revenue_from_status(status)
    except Exception as exc:
        print(json.dumps({"eligible": False, "error": str(exc)[:300]}, indent=2))
        return 1

    eligible = revenue >= min_rev
    out = {
        "eligible": eligible,
        "ledger_revenue_acp": format(revenue, "f"),
        "min_revenue_acp": format(min_rev, "f"),
        "v3_pool": args.v3_pool.lower(),
        "oracle_use_v3": None,
        "oracle_status": "not_checked",
        "revenue_window": "30d",
        "action": (
            "Approve fee tranche → wrap wACP → Add Liquidity on V3 (human-signed). "
            "Do not mint to the pool. Do not wash trade."
        ),
        "reasons": [
            (
                f"ledger revenue {revenue} ACP >= min {min_rev} ACP"
                if eligible
                else f"ledger revenue {revenue} ACP < min {min_rev} ACP — grow platform spend first"
            ),
            "keep WACP_ORACLE_USE_V3=false until quote_smoke passes",
        ],
        "treasury_url": args.base_url.rstrip("/") + "/treasury/status",
        "playbook": "docs/FINANCE_MODEL.md §7",
    }
    print(json.dumps(out, indent=2))
    return 0 if eligible else 2


if __name__ == "__main__":
    raise SystemExit(main())
