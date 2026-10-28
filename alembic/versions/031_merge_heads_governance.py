"""Merge Alembic heads after governance migration.

Revision ID: 031
Revises: 030, c5df567b5ed0
Create Date: 2026-04-24
"""

from typing import Sequence, Union


revision: str = "031"
down_revision: Union[str, Sequence[str], None] = ("030", "c5df567b5ed0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
