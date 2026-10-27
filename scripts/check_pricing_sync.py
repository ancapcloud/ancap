"""Check exact catalogue parity; independent of the caller's working directory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", type=Path, default=ROOT / "app/services/catalog_prices.json")
    parser.add_argument("--frontend", type=Path, default=ROOT / "frontend-app/src/lib/catalogPrices.json")
    args = parser.parse_args(argv)
    try:
        backend = json.loads(args.backend.read_text(encoding="utf-8"))
        frontend = json.loads(args.frontend.read_text(encoding="utf-8"))
        if not isinstance(backend, dict) or not isinstance(frontend, dict):
            raise ValueError("Both catalogues must be JSON objects")
        if not backend or not frontend:
            raise ValueError("Catalogues must not be empty")
    except (OSError, ValueError) as exc:
        print(f"Cannot verify catalogue parity: {exc}", file=sys.stderr)
        return 1

    missing = sorted(backend.keys() - frontend.keys())
    extra = sorted(frontend.keys() - backend.keys())
    changed = sorted(key for key in backend.keys() & frontend.keys() if backend[key] != frontend[key])
    for label, keys in (("Missing frontend keys", missing), ("Extra frontend keys", extra), ("Different prices", changed)):
        if keys:
            print(f"{label}: {', '.join(keys)}", file=sys.stderr)
    if missing or extra or changed:
        return 1
    print(f"Catalogue parity verified: {len(backend)} identical price entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
