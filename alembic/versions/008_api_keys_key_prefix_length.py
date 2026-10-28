"""Widen api_keys.key_prefix to 24 chars.

Revision ID: 008
Revises: 007
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import String
    op.alter_column(
        "api_keys",
        "key_prefix",
        existing_type=String(16),
        type_=String(24),
    )


def downgrade() -> None:
    from sqlalchemy import String
    op.alter_column(
        "api_keys",
        "key_prefix",
        existing_type=String(24),
        type_=String(16),
    )

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
