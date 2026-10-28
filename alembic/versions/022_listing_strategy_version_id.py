"""Listings: add strategy_version_id.

Revision ID: 022
Revises: 021
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("strategy_version_id", sa.dialects.postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.create_index("ix_listings_strategy_version_id", "listings", ["strategy_version_id"])
    op.create_foreign_key(
        "fk_listings_strategy_version_id",
        "listings",
        "strategy_versions",
        ["strategy_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_listings_strategy_version_id", "listings", type_="foreignkey")
    op.drop_index("ix_listings_strategy_version_id", table_name="listings")
    op.drop_column("listings", "strategy_version_id")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
