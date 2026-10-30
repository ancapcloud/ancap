"""add allocation source columns to workflow_cost_allocations

Revision ID: a72e12eb9246
Revises: 095_racp_redemptions
Create Date: 2026-10-30 07:03:28.298992

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a72e12eb9246"
down_revision = "095_racp_redemptions"
branch_labels = None
depends_on = None

_COST_CATEGORY = postgresql.ENUM(
    "model",
    "data",
    "infrastructure",
    "review",
    "support",
    "payment_fee",
    "creator_payout",
    name="costcategoryenum",
    create_type=False,
)


def upgrade() -> None:
    _COST_CATEGORY.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "workflow_cost_allocations",
        sa.Column("evidence_line_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "workflow_cost_allocations",
        sa.Column("evidence_amount", sa.Numeric(precision=36, scale=18), nullable=True),
    )
    op.add_column(
        "workflow_cost_allocations",
        sa.Column("category", _COST_CATEGORY, nullable=True),
    )
    op.add_column(
        "workflow_cost_allocations",
        sa.Column("currency", sa.String(length=3), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_cost_allocations", "currency")
    op.drop_column("workflow_cost_allocations", "category")
    op.drop_column("workflow_cost_allocations", "evidence_amount")
    op.drop_column("workflow_cost_allocations", "evidence_line_id")
    _COST_CATEGORY.drop(op.get_bind(), checkfirst=True)
