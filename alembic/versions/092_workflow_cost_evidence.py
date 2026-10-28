"""Operator-attested workflow cost source lines and atomic allocations."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "092_workflow_cost_evidence"
down_revision = "091_workflow_value"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("workflow_cost_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("document_id", sa.String(200), nullable=False),
        sa.Column("line_id", sa.String(100), nullable=False),
        sa.Column("document_sha256", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(36, 18), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=False),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("source", "document_id", "line_id", name="uq_workflow_cost_source_line"),
        sa.CheckConstraint("amount >= 0 AND amount != 'NaN'::numeric", name="ck_workflow_cost_amount"),
        sa.CheckConstraint("category IN ('model','data','infrastructure','review','support','payment_fee','creator_payout')", name="ck_workflow_cost_category"),
    )
    op.create_table("workflow_cost_allocations",
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_cost_evidence.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("amount", sa.Numeric(36, 18), nullable=False),
        sa.CheckConstraint("amount >= 0 AND amount != 'NaN'::numeric", name="ck_workflow_cost_allocation_amount"),
    )
    op.create_index("ix_workflow_cost_allocation_run", "workflow_cost_allocations", ["workflow_run_id"])


def downgrade():
    op.drop_index("ix_workflow_cost_allocation_run", table_name="workflow_cost_allocations")
    op.drop_table("workflow_cost_allocations")
    op.drop_table("workflow_cost_evidence")
