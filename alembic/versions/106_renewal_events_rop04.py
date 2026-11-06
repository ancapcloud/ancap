"""ROP-04: due renewal events with exact decimal amounts.

Revision ID: 106_renewal_events_rop04
Revises: 105_listing_promotions
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "106_renewal_events_rop04"
down_revision = "105_listing_promotions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "renewal_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", sa.String(255), nullable=False),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("subscription_id", sa.String(255), nullable=True),
        sa.Column("renewal_type", sa.String(20), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("renewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amount_due", sa.Numeric(36, 18), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payment_reference", sa.String(255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "recorded_by_user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_due >= 0 AND amount_due != 'NaN'::numeric", name="ck_renewal_amount"),
        sa.CheckConstraint("status IN ('pending', 'paid', 'failed', 'cancelled')", name="ck_renewal_status"),
        sa.CheckConstraint(
            "renewal_type IN ('monthly', 'quarterly', 'annual', 'license', 'one_off')",
            name="ck_renewal_type",
        ),
        sa.CheckConstraint("status <> 'paid' OR renewed_at IS NOT NULL", name="ck_renewal_paid_at"),
        sa.UniqueConstraint("project_id", "client_id", "subscription_id", "due_at", name="uq_renewal_event_due"),
    )
    op.create_index("ix_renewal_events_project_client", "renewal_events", ["project_id", "client_id"])
    op.create_index("ix_renewal_events_due_status", "renewal_events", ["due_at", "status"])


def downgrade():
    op.drop_index("ix_renewal_events_due_status", table_name="renewal_events")
    op.drop_index("ix_renewal_events_project_client", table_name="renewal_events")
    op.drop_table("renewal_events")
