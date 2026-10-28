"""Reputation 2.0: reputation_events, relationship_edges_daily, trust_scores, reputation_snapshots.

Revision ID: 004
Revises: 003
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reputation_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subject_type", sa.String(32), nullable=False, index=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("actor_type", sa.String(32), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("value", sa.Numeric(12, 6), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_reputation_events_subject_created",
        "reputation_events",
        ["subject_type", "subject_id", "created_at"],
    )

    op.create_table(
        "relationship_edges_daily",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("day", sa.Date(), nullable=False, index=True),
        sa.Column("src_type", sa.String(32), nullable=False),
        sa.Column("src_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("dst_type", sa.String(32), nullable=False),
        sa.Column("dst_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("edge_type", sa.String(32), nullable=False, index=True),
        sa.Column("count", sa.Integer(), server_default="0"),
        sa.Column("amount_sum", sa.Numeric(36, 18), nullable=True),
        sa.Column("unique_refs", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_relationship_edges_daily_day_src_dst",
        "relationship_edges_daily",
        ["day", "src_type", "src_id", "dst_type", "dst_id", "edge_type"],
        unique=True,
    )

    op.create_table(
        "trust_scores",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subject_type", sa.String(32), nullable=False, index=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("trust_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("components", postgresql.JSONB(), nullable=True),
        sa.Column("window", sa.String(16), nullable=False),
        sa.Column("algo_version", sa.String(32), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_trust_scores_subject_window",
        "trust_scores",
        ["subject_type", "subject_id", "window"],
        unique=True,
    )

    op.create_table(
        "reputation_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subject_type", sa.String(32), nullable=False, index=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("score", sa.Numeric(8, 4), nullable=False),
        sa.Column("components", postgresql.JSONB(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("algo_version", sa.String(32), nullable=False),
        sa.Column("window", sa.String(16), nullable=False),
        sa.Column("inputs_hash", sa.Text(), nullable=True),
        sa.Column("proof", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_reputation_snapshots_subject_window",
        "reputation_snapshots",
        ["subject_type", "subject_id", "window"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_reputation_snapshots_subject_window", "reputation_snapshots")
    op.drop_table("reputation_snapshots")
    op.drop_index("ix_trust_scores_subject_window", "trust_scores")
    op.drop_table("trust_scores")
    op.drop_index("ix_relationship_edges_daily_day_src_dst", "relationship_edges_daily")
    op.drop_table("relationship_edges_daily")
    op.drop_index("ix_reputation_events_subject_created", "reputation_events")
    op.drop_table("reputation_events")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
