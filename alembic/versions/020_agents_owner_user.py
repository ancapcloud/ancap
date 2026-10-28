"""Agents: owner_user_id (user-level ownership for golden paths).

Revision ID: 020
Revises: 019
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("owner_user_id", sa.dialects.postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.create_index("ix_agents_owner_user_id", "agents", ["owner_user_id"])
    op.create_foreign_key(
        "fk_agents_owner_user_id",
        "agents",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_agents_owner_user_id", "agents", type_="foreignkey")
    op.drop_index("ix_agents_owner_user_id", table_name="agents")
    op.drop_column("agents", "owner_user_id")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
