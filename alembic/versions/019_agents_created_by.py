"""Agents: created_by_agent_id (anti-sybil provenance).

Revision ID: 019
Revises: 018
Create Date: 2026-03-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("created_by_agent_id", sa.dialects.postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.create_index("ix_agents_created_by_agent_id", "agents", ["created_by_agent_id"])
    op.create_foreign_key(
        "fk_agents_created_by_agent_id",
        "agents",
        "agents",
        ["created_by_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_agents_created_by_agent_id", "agents", type_="foreignkey")
    op.drop_index("ix_agents_created_by_agent_id", table_name="agents")
    op.drop_column("agents", "created_by_agent_id")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
