"""Execution DAG (ROADMAP §5): run_steps step-level scoring (score_value, score_type).

Revision ID: 014
Revises: 013
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("run_steps", sa.Column("score_value", sa.Numeric(10, 4), nullable=True))
    op.add_column("run_steps", sa.Column("score_type", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("run_steps", "score_type")
    op.drop_column("run_steps", "score_value")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
