"""Fail when the Alembic revision graph has more than one head.

Multiple heads make ``alembic upgrade head`` fail on a fresh database, which
breaks deploys and test bootstrap. Run this in CI before the migration job.
"""

from __future__ import annotations

import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script_directory() -> ScriptDirectory:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return ScriptDirectory.from_config(config)


def get_heads() -> list[str]:
    return list(load_script_directory().get_heads())


def main() -> int:
    heads = sorted(get_heads())
    if len(heads) != 1:
        print(f"Alembic graph has {len(heads)} heads: {', '.join(heads)}")
        print("Merge them with: alembic merge -m '<reason>' " + " ".join(heads))
        return 1
    print(f"Alembic graph has a single head: {heads[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
