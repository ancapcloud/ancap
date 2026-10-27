"""Private immutable assessments of workflow result versions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "091_workflow_value"
down_revision = "090_qr_daily_counts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("workflow_result_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("result_hash", sa.String(64), nullable=False),
        sa.Column("result_snapshot_json", postgresql.JSONB(), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("baseline_minutes", sa.Numeric(12, 2)),
        sa.Column("assisted_minutes", sa.Numeric(12, 2)),
        sa.Column("hourly_rate", sa.Numeric(18, 6)),
        sa.Column("hourly_currency", sa.String(10)),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workflow_run_id", "result_hash", name="uq_workflow_assessment_version"),
        sa.CheckConstraint("verdict IN ('accepted', 'revision_requested', 'rejected')", name="ck_workflow_assessment_verdict"),
        sa.CheckConstraint("(baseline_minutes IS NULL) = (assisted_minutes IS NULL)", name="ck_workflow_assessment_time_pair"),
        sa.CheckConstraint("baseline_minutes >= 0 AND assisted_minutes >= 0", name="ck_workflow_assessment_nonnegative_time"),
        sa.CheckConstraint("(hourly_rate IS NULL) = (hourly_currency IS NULL)", name="ck_workflow_assessment_rate_pair"),
        sa.CheckConstraint("hourly_rate >= 0 AND (hourly_rate IS NULL OR baseline_minutes IS NOT NULL)", name="ck_workflow_assessment_rate_time"),
    )
    op.create_index("ix_workflow_assessment_owner_created", "workflow_result_assessments", ["owner_user_id", "created_at"])


def downgrade():
    op.drop_index("ix_workflow_assessment_owner_created", table_name="workflow_result_assessments")
    op.drop_table("workflow_result_assessments")
