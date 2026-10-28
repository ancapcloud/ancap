from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx


API_BASE = os.environ.get("ANCAP_API_BASE", "http://127.0.0.1:8001/v1").rstrip("/")
BEARER_TOKEN = os.environ.get("ANCAP_BEARER_TOKEN", "").strip()
PACKAGE_SLUG = os.environ.get("ANCAP_PACKAGE_SLUG", "launch-credits").strip() or "launch-credits"
CURRENCY = os.environ.get("ANCAP_CURRENCY", "USD").strip().upper() or "USD"


def require_env() -> None:
    if not BEARER_TOKEN:
        raise SystemExit("ANCAP_BEARER_TOKEN is required")


def api_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Idempotency-Key": f"example-stripe-topup-{int(time.time())}",
    }


def api_get(client: httpx.Client, path: str) -> dict[str, Any]:
    response = client.get(f"{API_BASE}{path}", headers={"Authorization": f"Bearer {BEARER_TOKEN}"})
    response.raise_for_status()
    return response.json()


def api_post(client: httpx.Client, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"{API_BASE}{path}", headers=api_headers(), json=payload)
    response.raise_for_status()
    return response.json()


def main() -> int:
    require_env()

    with httpx.Client(timeout=20.0) as client:
        packages = api_get(client, "/workflow-store/credit-packages")
        available = [item.get("slug") for item in packages.get("items", [])]
        print(f"Available packages: {available}")

        payload = {
            "package_slug": PACKAGE_SLUG,
            "currency": CURRENCY,
            "save_payment_method": True,
            "note": "examples/payment-integration/python_credit_topup.py",
        }
        created = api_post(client, "/payments/stripe/intent", payload)
        item = created["item"]
        stripe = created["stripe"]

        print("Created ANCAP Stripe top-up intent:")
        print(f"  intent_id: {item['id']}")
        print(f"  payment_reference: {item['payment_reference']}")
        print(f"  package: {created['package']['slug']}")
        print(f"  stripe_payment_intent_id: {stripe['payment_intent_id']}")
        print(f"  stripe_status: {stripe['status']}")
        print("  client_secret: [redacted; use only in the authorized checkout]")

        print("\nPolling ANCAP intent status 3 times (webhook-safe fallback example)...")
        for attempt in range(1, 4):
            polled = api_get(client, f"/payments/stripe/intents/{item['id']}")
            print(
                f"  poll {attempt}: status={polled['item']['status']} credited={polled['credited']} reference={polled['item']['payment_reference']}"
            )
            time.sleep(2)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip()
        print(f"API error {exc.response.status_code}: {body}", file=sys.stderr)
        raise SystemExit(1) from exc
