"""Merge workflow_cost_evidence branch heads."""

from alembic import op
import sqlalchemy as sa


revision = "094_merge_workflow_cost_heads"
down_revision = ("093_add_source_url_to_workflow_cost_evidence", "46f16ea4ae43")
branch_labels = None
depends_on = None


def upgrade():
    # Migration 093 already applied via down_revision chain
    # No additional schema changes needed - just marking merge point
    pass


def downgrade():
    # This is a merge, so downgrade is complex
    # For now, we'll skip this or handle carefully
    pass
