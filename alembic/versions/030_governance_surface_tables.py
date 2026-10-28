"""Governance surface tables.

Revision ID: 030
Revises: 029
Create Date: 2026-04-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "governance_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_governance_proposals_kind", "governance_proposals", ["kind"])
    op.create_index("ix_governance_proposals_target_type", "governance_proposals", ["target_type"])
    op.create_index("ix_governance_proposals_target_id", "governance_proposals", ["target_id"])
    op.create_index("ix_governance_proposals_status", "governance_proposals", ["status"])
    op.create_index("ix_governance_proposals_created_by", "governance_proposals", ["created_by"])
    op.create_index("ix_governance_proposals_reviewed_by", "governance_proposals", ["reviewed_by"])

    op.create_table(
        "governance_votes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "proposal_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("governance_proposals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("voter_type", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("voter_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("vote", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_governance_votes_proposal_id", "governance_votes", ["proposal_id"])
    op.create_index("ix_governance_votes_voter_id", "governance_votes", ["voter_id"])
    op.create_index(
        "uq_governance_vote_unique_voter",
        "governance_votes",
        ["proposal_id", "voter_type", "voter_id"],
        unique=True,
    )

    op.create_table(
        "governance_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "proposal_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("governance_proposals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column("actor_type", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("actor_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("event_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_governance_audit_log_proposal_id", "governance_audit_log", ["proposal_id"])
    op.create_index("ix_governance_audit_log_event_type", "governance_audit_log", ["event_type"])
    op.create_index("ix_governance_audit_log_actor_id", "governance_audit_log", ["actor_id"])

    op.create_table(
        "moderation_cases",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("opened_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_moderation_cases_subject_type", "moderation_cases", ["subject_type"])
    op.create_index("ix_moderation_cases_subject_id", "moderation_cases", ["subject_id"])
    op.create_index("ix_moderation_cases_reason_code", "moderation_cases", ["reason_code"])
    op.create_index("ix_moderation_cases_status", "moderation_cases", ["status"])
    op.create_index("ix_moderation_cases_opened_by", "moderation_cases", ["opened_by"])
    op.create_index("ix_moderation_cases_resolved_by", "moderation_cases", ["resolved_by"])


def downgrade() -> None:
    op.drop_index("ix_moderation_cases_resolved_by", table_name="moderation_cases")
    op.drop_index("ix_moderation_cases_opened_by", table_name="moderation_cases")
    op.drop_index("ix_moderation_cases_status", table_name="moderation_cases")
    op.drop_index("ix_moderation_cases_reason_code", table_name="moderation_cases")
    op.drop_index("ix_moderation_cases_subject_id", table_name="moderation_cases")
    op.drop_index("ix_moderation_cases_subject_type", table_name="moderation_cases")
    op.drop_table("moderation_cases")

    op.drop_index("ix_governance_audit_log_actor_id", table_name="governance_audit_log")
    op.drop_index("ix_governance_audit_log_event_type", table_name="governance_audit_log")
    op.drop_index("ix_governance_audit_log_proposal_id", table_name="governance_audit_log")
    op.drop_table("governance_audit_log")

    op.drop_index("uq_governance_vote_unique_voter", table_name="governance_votes")
    op.drop_index("ix_governance_votes_voter_id", table_name="governance_votes")
    op.drop_index("ix_governance_votes_proposal_id", table_name="governance_votes")
    op.drop_table("governance_votes")

    op.drop_index("ix_governance_proposals_reviewed_by", table_name="governance_proposals")
    op.drop_index("ix_governance_proposals_created_by", table_name="governance_proposals")
    op.drop_index("ix_governance_proposals_status", table_name="governance_proposals")
    op.drop_index("ix_governance_proposals_target_id", table_name="governance_proposals")
    op.drop_index("ix_governance_proposals_target_type", table_name="governance_proposals")
    op.drop_index("ix_governance_proposals_kind", table_name="governance_proposals")
    op.drop_table("governance_proposals")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
