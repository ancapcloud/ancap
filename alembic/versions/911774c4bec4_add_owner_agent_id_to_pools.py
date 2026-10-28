"""add owner_agent_id to pools

Revision ID: 911774c4bec4
Revises: c3e8f1b5d4a6
Create Date: 2026-05-24 21:13:44.092746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "911774c4bec4"
down_revision: Union[str, None] = "c3e8f1b5d4a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pools",
        sa.Column("owner_agent_id", sa.UUID(as_uuid=False), sa.ForeignKey("agents.id"), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_column("pools", "owner_agent_id")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
