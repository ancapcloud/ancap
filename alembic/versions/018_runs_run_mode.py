"""Execution runtime: runs.run_mode (mock | backtest) for explicit mode (PLAN §5).

Revision ID: 018
Revises: 017
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("run_mode", sa.String(16), nullable=False, server_default="mock"))


def downgrade() -> None:
    op.drop_column("runs", "run_mode")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
