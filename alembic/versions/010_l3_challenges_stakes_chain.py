"""L3: agent_challenges, agent_attestations, stakes, chain_anchors; agents.attestation_id, activated_at; ledger enum.

Revision ID: 010
Revises: 009
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New ledger event types for stake/unstake/slash
    op.execute("ALTER TYPE ledgereventtypeenum ADD VALUE IF NOT EXISTS 'stake'")
    op.execute("ALTER TYPE ledgereventtypeenum ADD VALUE IF NOT EXISTS 'unstake'")
    op.execute("ALTER TYPE ledgereventtypeenum ADD VALUE IF NOT EXISTS 'slash'")

    op.create_table(
        "agent_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("challenge_type", sa.String(32), nullable=False, index=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("nonce", sa.String(64), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "agent_attestations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("solution_hash", sa.String(64), nullable=False),
        sa.Column("attestation_sig", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["challenge_id"], ["agent_challenges.id"], ondelete="CASCADE"),
    )

    op.add_column(
        "agents",
        sa.Column("attestation_id", postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.add_column(
        "agents",
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_agents_attestation_id",
        "agents",
        "agent_attestations",
        ["attestation_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "stakes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("amount_currency", sa.String(10), nullable=False),
        sa.Column("amount_value", sa.Numeric(36, 18), nullable=False),
        sa.Column("status", sa.Enum("active", "released", "slashed", name="stakestatusenum"), nullable=False, server_default="active"),
        sa.Column("slash_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "chain_anchors",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("chain_id", sa.String(32), nullable=False, index=True),
        sa.Column("tx_hash", sa.String(128), nullable=True, index=True),
        sa.Column("payload_type", sa.String(32), nullable=False, index=True),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("anchored_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("chain_anchors")
    op.drop_table("stakes")
    op.execute("DROP TYPE IF EXISTS stakestatusenum")

    op.drop_constraint("fk_agents_attestation_id", "agents", type_="foreignkey")
    op.drop_column("agents", "activated_at")
    op.drop_column("agents", "attestation_id")

    op.drop_table("agent_attestations")
    op.drop_table("agent_challenges")

    # PostgreSQL: cannot remove enum values easily; leave ledgereventtypeenum as-is
    # op.execute("ALTER TYPE ledgereventtypeenum DROP VALUE 'stake'")  # not supported in PG

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
