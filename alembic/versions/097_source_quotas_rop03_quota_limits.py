"""add source_quotas table for request/retry quotas (ROP-03 subtask 2)

Revision ID: 097_source_quotas
Revises: 30fbd2048486
Create Date: 2026-11-01 01:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "097_source_quotas"
down_revision = "30fbd2048486"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("source_quotas"):
        return
    op.create_table(
        "source_quotas",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False, primary_key=True),
        sa.Column("project_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("requests_remaining", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("retries_remaining", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_request_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("project_id", name="uq_source_quotas_project"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("source_quotas"):
        op.drop_table("source_quotas")
