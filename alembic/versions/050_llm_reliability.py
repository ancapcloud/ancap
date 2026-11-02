"""Add LLM reliability fields: provider_status, failure_reason, retry_count.

Revision ID: afbea1ea0cd1
Revises: 049_org_webhook_models
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "afbea1ea0cd1"
down_revision = "049_org_webhook_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "llm_usage_events",
        sa.Column("provider_status", sa.String(32), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "llm_usage_events",
        sa.Column("failure_reason", sa.String(128), nullable=True),
    )
    op.add_column(
        "llm_usage_events",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute("CREATE INDEX ix_llm_usage_events_provider_status_idx ON llm_usage_events(provider_status)")
    op.execute("CREATE INDEX ix_llm_usage_events_failure_reason ON llm_usage_events(failure_reason)")


def downgrade() -> None:
    op.execute("DROP INDEX ix_llm_usage_events_provider_status_idx")
    op.execute("DROP INDEX ix_llm_usage_events_failure_reason")
    op.drop_column("llm_usage_events", "retry_count")
    op.drop_column("llm_usage_events", "failure_reason")
    op.drop_column("llm_usage_events", "provider_status")