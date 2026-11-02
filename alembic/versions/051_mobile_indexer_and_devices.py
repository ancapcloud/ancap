"""Add mobile ACP indexer (DB-backed tx history) and device registration for push.

Revision ID: e5f2d1a80b0c
Revises: afbea1ea0cd1
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e5f2d1a80b0c"
down_revision = "afbea1ea0cd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DB-backed ACP tx history per address (replaces full-chain scan)
    op.create_table(
        "mobile_acp_txs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("address", sa.String(64), nullable=False),
        sa.Column("txid", sa.String(128), nullable=False),
        sa.Column("block_height", sa.Integer(), nullable=True),
        sa.Column("block_time", sa.String(32), nullable=True),
        sa.Column("direction", sa.String(8), nullable=False),  # in | out | self
        sa.Column("sent_units", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("received_units", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("net_units", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("fee_units", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("confirmations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_tx_json", sa.JSON(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mobile_acp_txs_address_height", "mobile_acp_txs", ["address", "block_height"], unique=False)
    op.create_index("ix_mobile_acp_txs_address_created", "mobile_acp_txs", ["address", "scanned_at"], unique=False)
    op.create_index("ix_mobile_acp_txs_txid", "mobile_acp_txs", ["txid"], unique=True)

    # Push device registration for notifications
    op.create_table(
        "mobile_devices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("device_token", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),  # ios | android
        sa.Column("app_version", sa.String(16), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mobile_devices_user", "mobile_devices", ["user_id"])
    op.create_index("ix_mobile_devices_token", "mobile_devices", ["device_token"], unique=True)
    op.create_index("ix_mobile_devices_active", "mobile_devices", ["is_active"])

    op.create_table(
        "mobile_address_indexer_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_scanned_height", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("indexed_addresses", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("watermark", sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("mobile_address_indexer_state")
    op.drop_table("mobile_devices")
    op.drop_table("mobile_acp_txs")