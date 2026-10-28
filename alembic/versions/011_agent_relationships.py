"""Agent Graph Index (ROADMAP 2.1): agent_relationships for anti-sybil, reciprocity, cycles.

Revision ID: 011
Revises: 010
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("source_agent_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("target_agent_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("relation_type", sa.String(32), nullable=False),
        sa.Column("weight", sa.Numeric(36, 18), nullable=False, server_default="1"),
        sa.Column("ref_type", sa.String(32), nullable=True),
        sa.Column("ref_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_relationships_source_agent_id", "agent_relationships", ["source_agent_id"])
    op.create_index("ix_agent_relationships_target_agent_id", "agent_relationships", ["target_agent_id"])
    op.create_index("ix_agent_relationships_relation_type", "agent_relationships", ["relation_type"])
    op.create_index("ix_agent_relationships_ref_id", "agent_relationships", ["ref_id"])
    op.create_index(
        "ix_agent_relationships_pair_type",
        "agent_relationships",
        ["source_agent_id", "target_agent_id", "relation_type"],
    )
    op.create_index(
        "ix_agent_relationships_target",
        "agent_relationships",
        ["target_agent_id", "relation_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_relationships_target", "agent_relationships")
    op.drop_index("ix_agent_relationships_pair_type", "agent_relationships")
    op.drop_index("ix_agent_relationships_ref_id", "agent_relationships")
    op.drop_index("ix_agent_relationships_relation_type", "agent_relationships")
    op.drop_index("ix_agent_relationships_target_agent_id", "agent_relationships")
    op.drop_index("ix_agent_relationships_source_agent_id", "agent_relationships")
    op.drop_table("agent_relationships")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
