"""Execution DAG (ROADMAP §5): run_step_scores for alternative score_type (latency, quality).

Revision ID: 016
Revises: 015
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "run_step_scores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("run_step_id", sa.UUID(), nullable=False),
        sa.Column("score_type", sa.String(32), nullable=False),
        sa.Column("score_value", sa.Numeric(10, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_step_id"], ["run_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_step_id", "score_type", name="uq_run_step_scores_step_type"),
    )
    op.create_index("ix_run_step_scores_run_step_id", "run_step_scores", ["run_step_id"])


def downgrade() -> None:
    op.drop_index("ix_run_step_scores_run_step_id", table_name="run_step_scores")
    op.drop_table("run_step_scores")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
