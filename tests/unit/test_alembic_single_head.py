"""Guard against a branched Alembic graph (multiple heads)."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_graph_has_single_head() -> None:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    heads = list(ScriptDirectory.from_config(config).get_heads())
    assert len(heads) == 1, f"Merge Alembic heads before merging: {heads}"
