"""Bounded project sources, HTML versions and reviewed claim links."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "093_research_operations"
down_revision = "092_workflow_cost_evidence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("research_sources",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=False), sa.ForeignKey("workflow_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("permission_basis", sa.String(500), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("latest_hash", sa.String(64)),
        sa.Column("checked_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "url", name="uq_research_source_url"))
    op.create_index("ix_research_sources_project_id", "research_sources", ["project_id"])
    op.create_index("ix_research_sources_expires_at", "research_sources", ["expires_at"])
    op.create_table("research_snapshots",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("source_id", UUID(as_uuid=False), sa.ForeignKey("research_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_hash", sa.String(64), nullable=False),
        sa.Column("text_hash", sa.String(64), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("change_kind", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_research_snapshots_source_id", "research_snapshots", ["source_id"])
    op.create_table("research_claims",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("source_id", UUID(as_uuid=False), sa.ForeignKey("research_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("statement", sa.String(1000), nullable=False),
        sa.Column("excerpt", sa.String(500), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("reviewer_user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_research_claims_source_id", "research_claims", ["source_id"])


def downgrade():
    op.drop_table("research_claims")
    op.drop_table("research_snapshots")
    op.drop_table("research_sources")
