"""Paid "Sponsored" placement for marketplace listings.

Revision ID: 105_listing_promotions
Revises: 104_merge_packet_listing
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "105_listing_promotions"
down_revision = "104_merge_packet_listing"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "listing_promotions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "listing_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vertical_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("verticals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "owner_agent_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "purchased_by_user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_value", sa.Numeric(36, 18), nullable=False),
        sa.Column("amount_currency", sa.String(16), nullable=False),
        sa.Column(
            "ledger_event_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("ledger_events.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("days > 0", name="ck_listing_promotions_days_positive"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_listing_promotions_window"),
    )
    op.create_index("ix_listing_promotions_listing_ends", "listing_promotions", ["listing_id", "ends_at"])
    op.create_index("ix_listing_promotions_vertical_ends", "listing_promotions", ["vertical_id", "ends_at"])


def downgrade():
    op.drop_index("ix_listing_promotions_vertical_ends", table_name="listing_promotions")
    op.drop_index("ix_listing_promotions_listing_ends", table_name="listing_promotions")
    op.drop_table("listing_promotions")
