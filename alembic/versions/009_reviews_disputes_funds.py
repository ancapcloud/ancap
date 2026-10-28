"""L2: reviews, disputes, funds, fund_allocations.

Revision ID: 009
Revises: 008
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("reviewer_type", sa.String(20), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("target_type", sa.String(32), nullable=False, index=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("weight", sa.Numeric(5, 4), nullable=False, server_default="1"),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_reviews_target", "reviews", ["target_type", "target_id"], unique=False)

    op.create_table(
        "disputes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open", index=True),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("verdict", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "funds",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, index=True),
        sa.Column("owner_agent_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("pool_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["owner_agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["pool_id"], ["pools.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "fund_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("fund_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("strategy_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("weight", sa.Numeric(5, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_version_id"], ["strategy_versions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_fund_allocations_fund", "fund_allocations", ["fund_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_fund_allocations_fund", table_name="fund_allocations")
    op.drop_table("fund_allocations")
    op.drop_table("funds")
    op.drop_table("disputes")
    op.drop_index("ix_reviews_target", table_name="reviews")
    op.drop_table("reviews")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
