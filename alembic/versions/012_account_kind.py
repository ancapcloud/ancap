"""Ledger (ROADMAP §3): account_kind for system account types (treasury, fees, escrow, burn, external).

Revision ID: 012
Revises: 011
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("account_kind", sa.String(20), nullable=True))
    op.create_index("ix_accounts_account_kind", "accounts", ["account_kind"], unique=False)

    # Backfill: system -> fees, order_escrow/stake_escrow -> escrow, pool_treasury -> treasury
    op.execute("UPDATE accounts SET account_kind = 'fees' WHERE owner_type = 'system'")
    op.execute("UPDATE accounts SET account_kind = 'escrow' WHERE owner_type IN ('order_escrow', 'stake_escrow')")
    op.execute("UPDATE accounts SET account_kind = 'treasury' WHERE owner_type = 'pool_treasury'")


def downgrade() -> None:
    op.drop_index("ix_accounts_account_kind", table_name="accounts")
    op.drop_column("accounts", "account_kind")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
