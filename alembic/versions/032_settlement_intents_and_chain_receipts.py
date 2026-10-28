"""Add settlement intents and chain receipts.

Revision ID: 032
Revises: 031
Create Date: 2026-04-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "032"
down_revision: Union[str, Sequence[str], None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settlement_intents",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("intent_type", sa.String(length=32), nullable=False),
        sa.Column("source_owner_type", sa.String(length=32), nullable=False),
        sa.Column("source_owner_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("target_owner_type", sa.String(length=32), nullable=False),
        sa.Column("target_owner_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("amount_currency", sa.String(length=10), nullable=False),
        sa.Column("amount_value", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_settlement_intents_amount_currency"), "settlement_intents", ["amount_currency"], unique=False)
    op.create_index(op.f("ix_settlement_intents_correlation_id"), "settlement_intents", ["correlation_id"], unique=False)
    op.create_index(op.f("ix_settlement_intents_intent_type"), "settlement_intents", ["intent_type"], unique=False)
    op.create_index(op.f("ix_settlement_intents_source_owner_id"), "settlement_intents", ["source_owner_id"], unique=False)
    op.create_index(op.f("ix_settlement_intents_status"), "settlement_intents", ["status"], unique=False)
    op.create_index(op.f("ix_settlement_intents_target_owner_id"), "settlement_intents", ["target_owner_id"], unique=False)
    op.create_index("uq_settlement_intents_correlation_id", "settlement_intents", ["correlation_id"], unique=True)

    op.create_table(
        "chain_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("settlement_intent_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("chain_id", sa.String(length=32), nullable=False),
        sa.Column("tx_hash", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("receipt_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["settlement_intent_id"], ["settlement_intents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chain_receipts_chain_id"), "chain_receipts", ["chain_id"], unique=False)
    op.create_index(op.f("ix_chain_receipts_correlation_id"), "chain_receipts", ["correlation_id"], unique=False)
    op.create_index(op.f("ix_chain_receipts_settlement_intent_id"), "chain_receipts", ["settlement_intent_id"], unique=False)
    op.create_index(op.f("ix_chain_receipts_status"), "chain_receipts", ["status"], unique=False)
    op.create_index(op.f("ix_chain_receipts_tx_hash"), "chain_receipts", ["tx_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chain_receipts_tx_hash"), table_name="chain_receipts")
    op.drop_index(op.f("ix_chain_receipts_status"), table_name="chain_receipts")
    op.drop_index(op.f("ix_chain_receipts_settlement_intent_id"), table_name="chain_receipts")
    op.drop_index(op.f("ix_chain_receipts_correlation_id"), table_name="chain_receipts")
    op.drop_index(op.f("ix_chain_receipts_chain_id"), table_name="chain_receipts")
    op.drop_table("chain_receipts")

    op.drop_index("uq_settlement_intents_correlation_id", table_name="settlement_intents")
    op.drop_index(op.f("ix_settlement_intents_target_owner_id"), table_name="settlement_intents")
    op.drop_index(op.f("ix_settlement_intents_status"), table_name="settlement_intents")
    op.drop_index(op.f("ix_settlement_intents_source_owner_id"), table_name="settlement_intents")
    op.drop_index(op.f("ix_settlement_intents_intent_type"), table_name="settlement_intents")
    op.drop_index(op.f("ix_settlement_intents_correlation_id"), table_name="settlement_intents")
    op.drop_index(op.f("ix_settlement_intents_amount_currency"), table_name="settlement_intents")
    op.drop_table("settlement_intents")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
