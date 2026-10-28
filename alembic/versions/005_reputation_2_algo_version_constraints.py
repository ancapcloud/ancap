"""Reputation 2.0: unique by algo_version, inputs_hash, meta, CheckConstraints, indexes.

Revision ID: 005
Revises: 004
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- trust_scores: add inputs_hash, drop old unique, add new unique with algo_version, add check ---
    op.add_column("trust_scores", sa.Column("inputs_hash", sa.String(64), nullable=True))
    op.drop_index("ix_trust_scores_subject_window", table_name="trust_scores")
    op.create_index(
        "uq_trust_scores_subject_window_algo",
        "trust_scores",
        ["subject_type", "subject_id", "window", "algo_version"],
        unique=True,
    )
    op.create_check_constraint("ck_trust_score_0_1", "trust_scores", "trust_score >= 0 AND trust_score <= 1")

    # --- reputation_snapshots: drop old unique, add new unique with algo_version, add check ---
    op.drop_index("ix_reputation_snapshots_subject_window", table_name="reputation_snapshots")
    op.create_index(
        "uq_rep_snapshots_subject_window_algo",
        "reputation_snapshots",
        ["subject_type", "subject_id", "window", "algo_version"],
        unique=True,
    )
    op.create_check_constraint("ck_rep_score_0_100", "reputation_snapshots", "score >= 0 AND score <= 100")

    # --- relationship_edges_daily: add meta, add performance indexes ---
    op.add_column(
        "relationship_edges_daily",
        sa.Column("meta", postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_edges_daily_src_day", "relationship_edges_daily", ["src_type", "src_id", "day"], unique=False)
    op.create_index("ix_edges_daily_dst_day", "relationship_edges_daily", ["dst_type", "dst_id", "day"], unique=False)
    op.create_index(
        "ix_edges_daily_pair_day",
        "relationship_edges_daily",
        ["src_type", "src_id", "dst_type", "dst_id", "day"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_edges_daily_pair_day", table_name="relationship_edges_daily")
    op.drop_index("ix_edges_daily_dst_day", table_name="relationship_edges_daily")
    op.drop_index("ix_edges_daily_src_day", table_name="relationship_edges_daily")
    op.drop_column("relationship_edges_daily", "meta")

    op.drop_constraint("ck_rep_score_0_100", "reputation_snapshots", type_="check")
    op.drop_index("uq_rep_snapshots_subject_window_algo", table_name="reputation_snapshots")
    op.create_index(
        "ix_reputation_snapshots_subject_window",
        "reputation_snapshots",
        ["subject_type", "subject_id", "window"],
        unique=True,
    )

    op.drop_constraint("ck_trust_score_0_1", "trust_scores", type_="check")
    op.drop_index("uq_trust_scores_subject_window_algo", table_name="trust_scores")
    op.create_index(
        "ix_trust_scores_subject_window",
        "trust_scores",
        ["subject_type", "subject_id", "window"],
        unique=True,
    )
    op.drop_column("trust_scores", "inputs_hash")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
