"""Execution DAG (ROADMAP §5): run_steps.context_after for replay from step N.

Revision ID: 015
Revises: 014
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("run_steps", sa.Column("context_after", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("run_steps", "context_after")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
