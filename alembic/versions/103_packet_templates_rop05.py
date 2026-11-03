"""ROP-05: reusable packet templates (categories/structure only).

Distinct from onboarding templates. Revises the numbered mainline tip
``102_cost_evidence_attribution``.

Revision ID: 103_packet_templates_rop05
Revises: 102_cost_evidence_attribution
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "103_packet_templates_rop05"
down_revision: Union[str, Sequence[str], None] = "102_cost_evidence_attribution"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "packet_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "source_categories",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("max_sources_per_packet", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_snapshots_per_source", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("max_claims_per_source", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("check_cooldown_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column(
            "packet_structure",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("languages", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name="fk_packet_templates_owner_user",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_packet_template_slug"),
    )
    op.create_index("ix_packet_templates_created", "packet_templates", ["created_at"])
    op.create_index("ix_packet_templates_owner", "packet_templates", ["owner_user_id"])
    op.create_index("ix_packet_templates_status", "packet_templates", ["status"])


def downgrade() -> None:
    op.drop_index("ix_packet_templates_status", table_name="packet_templates")
    op.drop_index("ix_packet_templates_owner", table_name="packet_templates")
    op.drop_index("ix_packet_templates_created", table_name="packet_templates")
    op.drop_table("packet_templates")
