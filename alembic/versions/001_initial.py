"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=True),
        sa.Column("roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Enum("active", "suspended", "quarantined", name="agentstatusenum"), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "agent_profiles",
        sa.Column("agent_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("agent_id"),
    )

    op.create_table(
        "verticals",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("status", sa.Enum("proposed", "approved", "active", "deprecated", "rejected", name="verticalstatusenum"), nullable=True),
        sa.Column("owner_agent_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verticals_name", "verticals", ["name"], unique=False)

    op.create_table(
        "vertical_specs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("vertical_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("spec_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vertical_id"], ["verticals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "strategies",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("vertical_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.Enum("draft", "published", "paused", "retired", name="strategystatusenum"), nullable=True),
        sa.Column("owner_agent_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("summary", sa.String(300), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["vertical_id"], ["verticals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategies_name", "strategies", ["name"], unique=False)

    op.create_table(
        "strategy_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("semver", sa.String(32), nullable=False),
        sa.Column("workflow_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("param_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("strategy_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("fee_model", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Enum("active", "inactive", "suspended", name="listingstatusenum"), nullable=True),
        sa.Column("terms_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pools",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("risk_profile", sa.Enum("low", "medium", "high", "experimental", name="riskprofileenum"), nullable=False),
        sa.Column("status", sa.Enum("active", "halted", "archived", name="poolstatusenum"), nullable=True),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fee_model", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pools_name", "pools", ["name"], unique=False)

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("owner_type", sa.String(20), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounts_owner_type_id", "accounts", ["owner_type", "owner_id"], unique=True)
    op.create_index("ix_accounts_owner_id", "accounts", ["owner_id"], unique=False)

    op.create_table(
        "ledger_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", sa.Enum("deposit", "withdraw", "allocate", "deallocate", "pnl", "fee", "refund", "transfer", name="ledgereventtypeenum"), nullable=False),
        sa.Column("amount_currency", sa.String(10), nullable=False),
        sa.Column("amount_value", sa.Numeric(36, 18), nullable=False),
        sa.Column("src_account_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("dst_account_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["dst_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["src_account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("buyer_type", sa.String(20), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.Enum("pending", "paid", "failed", "cancelled", "refunded", name="orderstatusenum"), nullable=True),
        sa.Column("amount_currency", sa.String(10), nullable=True),
        sa.Column("amount_value", sa.Numeric(36, 18), nullable=True),
        sa.Column("payment_method", sa.String(64), nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "access_grants",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("grantee_type", sa.String(20), nullable=False),
        sa.Column("grantee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scope", sa.Enum("view", "execute", "allocate", name="accessscopeenum"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("strategy_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("pool_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("state", sa.Enum("queued", "running", "succeeded", "failed", "killed", name="runstateenum"), nullable=True),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("limits", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dry_run", sa.Boolean(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["pool_id"], ["pools.id"]),
        sa.ForeignKeyConstraint(["strategy_version_id"], ["strategy_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "run_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "metrics",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metrics_name", "metrics", ["name"], unique=False)

    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("strategy_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("percentile_in_vertical", sa.Numeric(5, 4), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["strategy_version_id"], ["strategy_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shares",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("pool_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("share_balance", sa.Numeric(36, 18), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["pool_id"], ["pools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "risk_policies",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("policy_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "circuit_breakers",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("state", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reputations",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subject_type", sa.String(32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reputations_subject", "reputations", ["subject_type", "subject_id"], unique=True)
    op.create_index("ix_reputations_subject_id", "reputations", ["subject_id"], unique=False)


def downgrade() -> None:
    op.drop_table("reputations")
    op.drop_table("circuit_breakers")
    op.drop_table("risk_policies")
    op.drop_table("shares")
    op.drop_table("evaluations")
    op.drop_table("metrics")
    op.drop_table("run_logs")
    op.drop_table("runs")
    op.drop_table("access_grants")
    op.drop_table("orders")
    op.drop_table("ledger_events")
    op.drop_table("accounts")
    op.drop_table("pools")
    op.drop_table("listings")
    op.drop_table("strategy_versions")
    op.drop_table("strategies")
    op.drop_table("vertical_specs")
    op.drop_table("verticals")
    op.drop_table("agent_profiles")
    op.drop_table("agents")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS runstateenum")
    op.execute("DROP TYPE IF EXISTS accessscopeenum")
    op.execute("DROP TYPE IF EXISTS orderstatusenum")
    op.execute("DROP TYPE IF EXISTS ledgereventtypeenum")
    op.execute("DROP TYPE IF EXISTS poolstatusenum")
    op.execute("DROP TYPE IF EXISTS riskprofileenum")
    op.execute("DROP TYPE IF EXISTS listingstatusenum")
    op.execute("DROP TYPE IF EXISTS strategystatusenum")
    op.execute("DROP TYPE IF EXISTS verticalstatusenum")
    op.execute("DROP TYPE IF EXISTS agentstatusenum")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
