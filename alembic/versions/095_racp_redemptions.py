"""rACP → ACP redemption ops + transitions (exclusive reserve rail).

Revision ID: 095_racp_redemptions
Revises: 092_add_workflow_cost_allocations, 094_merge_workflow_cost_heads
Create Date: 2026-10-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "095_racp_redemptions"
down_revision = ("092_add_workflow_cost_allocations", "094_merge_workflow_cost_heads")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "racp_redemptions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("redemption_id", sa.BigInteger(), nullable=False),
        sa.Column("holder", sa.String(length=66), nullable=False),
        sa.Column("amount_racp_wei", sa.Numeric(precision=38, scale=0), nullable=False),
        sa.Column("amount_acp_smallest", sa.Numeric(precision=38, scale=0), nullable=False),
        sa.Column("user_acp_address", sa.String(length=128), nullable=False),
        sa.Column("rh_chain_id", sa.String(length=32), nullable=False, server_default="4663"),
        sa.Column("rh_tx_hash", sa.String(length=128), nullable=False),
        sa.Column("rh_log_index", sa.Integer(), nullable=False),
        sa.Column("rh_block_number", sa.BigInteger(), nullable=True),
        sa.Column("acp_chain_id", sa.String(length=32), nullable=False, server_default="acp"),
        sa.Column("acp_tx_hash", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("redemption_id", name="ux_racp_redemptions_onchain_id"),
    )
    op.create_index("ix_racp_redemptions_status", "racp_redemptions", ["status"], unique=False)
    op.create_index("ix_racp_redemptions_created", "racp_redemptions", ["created_at"], unique=False)
    op.create_index(
        "ux_racp_redemptions_rh_log",
        "racp_redemptions",
        ["rh_chain_id", "rh_tx_hash", "rh_log_index"],
        unique=True,
    )
    op.create_index(
        "ux_racp_redemptions_acp_tx",
        "racp_redemptions",
        ["acp_chain_id", "acp_tx_hash"],
        unique=True,
        postgresql_where=sa.text("acp_tx_hash IS NOT NULL"),
    )

    op.create_table(
        "racp_redemption_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("redemption_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("from_status", sa.String(length=40), nullable=True),
        sa.Column("to_status", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["redemption_id"], ["racp_redemptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_racp_redemption_transitions_op",
        "racp_redemption_transitions",
        ["redemption_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_racp_redemption_transitions_op", table_name="racp_redemption_transitions")
    op.drop_table("racp_redemption_transitions")
    op.drop_index("ux_racp_redemptions_acp_tx", table_name="racp_redemptions")
    op.drop_index("ux_racp_redemptions_rh_log", table_name="racp_redemptions")
    op.drop_index("ix_racp_redemptions_created", table_name="racp_redemptions")
    op.drop_index("ix_racp_redemptions_status", table_name="racp_redemptions")
    op.drop_table("racp_redemptions")
