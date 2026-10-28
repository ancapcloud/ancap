"""Sprint-3 growth layer tables.

Revision ID: 029
Revises: 028
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "referral_codes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("reward_bps", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ux_referral_codes_code", "referral_codes", ["code"], unique=True)
    op.create_index("ix_referral_codes_owner_user", "referral_codes", ["owner_user_id"])
    op.create_index("ix_referral_codes_owner_agent", "referral_codes", ["owner_agent_id"])

    op.create_table(
        "referral_attributions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "referral_code_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("referral_codes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("referred_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("referred_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("attributed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="signup"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    op.create_index("ix_referral_attributions_code", "referral_attributions", ["referral_code_id"])
    op.create_index("ix_referral_attributions_referred_user", "referral_attributions", ["referred_user_id"])
    op.create_index("ix_referral_attributions_referred_agent", "referral_attributions", ["referred_agent_id"])
    # ensure at most one attribution per referred user/agent
    op.create_index(
        "ux_referral_attributions_referred_user_unique",
        "referral_attributions",
        ["referred_user_id"],
        unique=True,
        postgresql_where=sa.text("referred_user_id IS NOT NULL"),
    )
    op.create_index(
        "ux_referral_attributions_referred_agent_unique",
        "referral_attributions",
        ["referred_agent_id"],
        unique=True,
        postgresql_where=sa.text("referred_agent_id IS NOT NULL"),
    )

    op.create_table(
        "referral_reward_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "referral_attribution_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("referral_attributions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("beneficiary_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("beneficiary_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("trigger_ref_type", sa.String(length=32), nullable=False),
        sa.Column("trigger_ref_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("amount_value", sa.Numeric(38, 18), nullable=False),
        sa.Column("ledger_tx_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("ledger_events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ref_reward_attribution", "referral_reward_events", ["referral_attribution_id"])
    op.create_index("ix_ref_reward_benef_user", "referral_reward_events", ["beneficiary_user_id"])
    op.create_index("ix_ref_reward_benef_agent", "referral_reward_events", ["beneficiary_agent_id"])
    op.create_index(
        "ux_ref_reward_dedupe",
        "referral_reward_events",
        ["referral_attribution_id", "trigger_type", "trigger_ref_type", "trigger_ref_id"],
        unique=True,
    )

    op.create_table(
        "faucet_claims",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("amount_value", sa.Numeric(38, 18), nullable=False),
        sa.Column("claim_status", sa.String(length=32), nullable=False, server_default="granted"),
        sa.Column("risk_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ledger_tx_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("ledger_events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_faucet_claims_user", "faucet_claims", ["user_id"])
    op.create_index("ix_faucet_claims_agent", "faucet_claims", ["agent_id"])
    op.create_index("ix_faucet_claims_created_at", "faucet_claims", ["created_at"])
    # allow exactly one successful claim per user (anti-abuse v1)
    op.create_index(
        "ux_faucet_claims_user_once",
        "faucet_claims",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL AND claim_status = 'granted'"),
    )

    op.create_table(
        "starter_packs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ux_starter_packs_code", "starter_packs", ["code"], unique=True)

    op.create_table(
        "starter_pack_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "starter_pack_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("starter_packs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="assigned"),
    )
    op.create_index("ix_sp_assign_pack", "starter_pack_assignments", ["starter_pack_id"])
    op.create_index("ix_sp_assign_user", "starter_pack_assignments", ["user_id"])
    op.create_index("ix_sp_assign_agent", "starter_pack_assignments", ["agent_id"])
    op.create_index(
        "ux_sp_assign_pack_user_once",
        "starter_pack_assignments",
        ["starter_pack_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )

    op.create_table(
        "strategy_follows",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("follower_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("follower_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_strategy_follows_strategy", "strategy_follows", ["strategy_id"])
    op.create_index("ix_strategy_follows_user", "strategy_follows", ["follower_user_id"])
    op.create_index("ix_strategy_follows_agent", "strategy_follows", ["follower_agent_id"])
    op.create_index(
        "ux_strategy_follows_user_active",
        "strategy_follows",
        ["strategy_id", "follower_user_id"],
        unique=True,
        postgresql_where=sa.text("follower_user_id IS NOT NULL AND is_active = true"),
    )
    op.create_index(
        "ux_strategy_follows_agent_active",
        "strategy_follows",
        ["strategy_id", "follower_agent_id"],
        unique=True,
        postgresql_where=sa.text("follower_agent_id IS NOT NULL AND is_active = true"),
    )

    op.create_table(
        "strategy_copies",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("source_strategy_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("copied_strategy_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("copier_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("copier_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("copy_mode", sa.String(length=32), nullable=False, server_default="fork"),
    )
    op.create_index("ix_strategy_copies_source", "strategy_copies", ["source_strategy_id"])
    op.create_index("ix_strategy_copies_copied", "strategy_copies", ["copied_strategy_id"])
    op.create_index("ix_strategy_copies_user", "strategy_copies", ["copier_user_id"])
    op.create_index("ix_strategy_copies_agent", "strategy_copies", ["copier_agent_id"])
    op.create_index(
        "ux_strategy_copies_lineage",
        "strategy_copies",
        ["source_strategy_id", "copied_strategy_id"],
        unique=True,
    )

    op.create_table(
        "agent_follows",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("target_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("follower_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("follower_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_agent_follows_target", "agent_follows", ["target_agent_id"])
    op.create_index("ix_agent_follows_user", "agent_follows", ["follower_user_id"])
    op.create_index("ix_agent_follows_agent", "agent_follows", ["follower_agent_id"])
    op.create_index(
        "ux_agent_follows_user_active",
        "agent_follows",
        ["target_agent_id", "follower_user_id"],
        unique=True,
        postgresql_where=sa.text("follower_user_id IS NOT NULL AND is_active = true"),
    )
    op.create_index(
        "ux_agent_follows_agent_active",
        "agent_follows",
        ["target_agent_id", "follower_agent_id"],
        unique=True,
        postgresql_where=sa.text("follower_agent_id IS NOT NULL AND is_active = true"),
    )

    op.create_table(
        "notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recipient_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_user", "notification_events", ["recipient_user_id"])
    op.create_index("ix_notifications_agent", "notification_events", ["recipient_agent_id"])
    op.create_index("ix_notifications_created_at", "notification_events", ["created_at"])
    op.create_index("ux_notifications_dedupe", "notification_events", ["dedupe_key"], unique=True, postgresql_where=sa.text("dedupe_key IS NOT NULL"))

    op.create_table(
        "public_activity_feed",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("actor_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("ref_type", sa.String(length=32), nullable=False),
        sa.Column("ref_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False, server_default="public"),
        sa.Column("score", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_public_feed_event_type", "public_activity_feed", ["event_type"])
    op.create_index("ix_public_feed_ref", "public_activity_feed", ["ref_type", "ref_id"])
    op.create_index("ix_public_feed_visibility", "public_activity_feed", ["visibility"])
    op.create_index("ix_public_feed_created_at", "public_activity_feed", ["created_at"])
    op.create_index("ix_public_feed_score_created", "public_activity_feed", ["score", "created_at"])
    op.create_index("ix_public_feed_actor_agent_created", "public_activity_feed", ["actor_agent_id", "created_at"])

    op.create_table(
        "leaderboard_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("board_type", sa.String(length=32), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("window", sa.String(length=16), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(18, 6), nullable=False),
        sa.Column("components_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "ux_leaderboard_unique",
        "leaderboard_snapshots",
        ["board_type", "subject_type", "subject_id", "window", "snapshot_date"],
        unique=True,
    )
    op.create_index("ix_leaderboard_lookup", "leaderboard_snapshots", ["board_type", "window", "snapshot_date", "rank"])
    op.create_index("ix_leaderboard_subject", "leaderboard_snapshots", ["subject_type", "subject_id"])

    op.create_table(
        "growth_metric_rollups",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("metric_value", sa.Numeric(38, 10), nullable=False),
        sa.Column("dimensions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("dimensions_hash", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_growth_metric_date", "growth_metric_rollups", ["metric_date"])
    op.create_index("ix_growth_metric_key", "growth_metric_rollups", ["metric_key"])
    op.create_index("ix_growth_metric_key_date", "growth_metric_rollups", ["metric_key", "metric_date"])
    op.create_index("ix_growth_metric_dimensions_hash", "growth_metric_rollups", ["dimensions_hash"])
    op.create_index("ux_growth_metric_unique", "growth_metric_rollups", ["metric_date", "metric_key", "dimensions_hash"], unique=True)

    op.create_table(
        "task_feed_items",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reward_currency", sa.String(length=16), nullable=True),
        sa.Column("reward_amount_value", sa.Numeric(38, 18), nullable=True),
        sa.Column("target_agent_type", sa.String(length=64), nullable=True),
        sa.Column("target_vertical", sa.String(length=64), nullable=True),
        sa.Column("eligibility_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("score", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_task_feed_source", "task_feed_items", ["source_type", "source_id"])
    op.create_index("ix_task_feed_task_type", "task_feed_items", ["task_type"])
    op.create_index("ix_task_feed_vertical", "task_feed_items", ["target_vertical"])
    op.create_index("ix_task_feed_status", "task_feed_items", ["status"])
    op.create_index("ix_task_feed_created_at", "task_feed_items", ["created_at"])
    op.create_index("ix_task_feed_open_score", "task_feed_items", ["status", "score", "created_at"])
    op.create_index("ix_task_feed_vertical_status_score", "task_feed_items", ["target_vertical", "status", "score"])

    op.alter_column("growth_metric_rollups", "dimensions_hash", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_task_feed_vertical_status_score", table_name="task_feed_items")
    op.drop_index("ix_task_feed_open_score", table_name="task_feed_items")
    op.drop_index("ix_task_feed_created_at", table_name="task_feed_items")
    op.drop_index("ix_task_feed_status", table_name="task_feed_items")
    op.drop_index("ix_task_feed_vertical", table_name="task_feed_items")
    op.drop_index("ix_task_feed_task_type", table_name="task_feed_items")
    op.drop_index("ix_task_feed_source", table_name="task_feed_items")
    op.drop_table("task_feed_items")

    op.drop_index("ux_growth_metric_unique", table_name="growth_metric_rollups")
    op.drop_index("ix_growth_metric_dimensions_hash", table_name="growth_metric_rollups")
    op.drop_index("ix_growth_metric_key_date", table_name="growth_metric_rollups")
    op.drop_index("ix_growth_metric_key", table_name="growth_metric_rollups")
    op.drop_index("ix_growth_metric_date", table_name="growth_metric_rollups")
    op.drop_table("growth_metric_rollups")

    op.drop_index("ix_leaderboard_subject", table_name="leaderboard_snapshots")
    op.drop_index("ix_leaderboard_lookup", table_name="leaderboard_snapshots")
    op.drop_index("ux_leaderboard_unique", table_name="leaderboard_snapshots")
    op.drop_table("leaderboard_snapshots")

    op.drop_index("ix_public_feed_actor_agent_created", table_name="public_activity_feed")
    op.drop_index("ix_public_feed_score_created", table_name="public_activity_feed")
    op.drop_index("ix_public_feed_created_at", table_name="public_activity_feed")
    op.drop_index("ix_public_feed_visibility", table_name="public_activity_feed")
    op.drop_index("ix_public_feed_ref", table_name="public_activity_feed")
    op.drop_index("ix_public_feed_event_type", table_name="public_activity_feed")
    op.drop_table("public_activity_feed")

    op.drop_index("ux_notifications_dedupe", table_name="notification_events")
    op.drop_index("ix_notifications_created_at", table_name="notification_events")
    op.drop_index("ix_notifications_agent", table_name="notification_events")
    op.drop_index("ix_notifications_user", table_name="notification_events")
    op.drop_table("notification_events")

    op.drop_index("ux_agent_follows_agent_active", table_name="agent_follows")
    op.drop_index("ux_agent_follows_user_active", table_name="agent_follows")
    op.drop_index("ix_agent_follows_agent", table_name="agent_follows")
    op.drop_index("ix_agent_follows_user", table_name="agent_follows")
    op.drop_index("ix_agent_follows_target", table_name="agent_follows")
    op.drop_table("agent_follows")

    op.drop_index("ux_strategy_copies_lineage", table_name="strategy_copies")
    op.drop_index("ix_strategy_copies_agent", table_name="strategy_copies")
    op.drop_index("ix_strategy_copies_user", table_name="strategy_copies")
    op.drop_index("ix_strategy_copies_copied", table_name="strategy_copies")
    op.drop_index("ix_strategy_copies_source", table_name="strategy_copies")
    op.drop_table("strategy_copies")

    op.drop_index("ux_strategy_follows_agent_active", table_name="strategy_follows")
    op.drop_index("ux_strategy_follows_user_active", table_name="strategy_follows")
    op.drop_index("ix_strategy_follows_agent", table_name="strategy_follows")
    op.drop_index("ix_strategy_follows_user", table_name="strategy_follows")
    op.drop_index("ix_strategy_follows_strategy", table_name="strategy_follows")
    op.drop_table("strategy_follows")

    op.drop_index("ux_sp_assign_pack_user_once", table_name="starter_pack_assignments")
    op.drop_index("ix_sp_assign_agent", table_name="starter_pack_assignments")
    op.drop_index("ix_sp_assign_user", table_name="starter_pack_assignments")
    op.drop_index("ix_sp_assign_pack", table_name="starter_pack_assignments")
    op.drop_table("starter_pack_assignments")

    op.drop_index("ux_starter_packs_code", table_name="starter_packs")
    op.drop_table("starter_packs")

    op.drop_index("ux_faucet_claims_user_once", table_name="faucet_claims")
    op.drop_index("ix_faucet_claims_created_at", table_name="faucet_claims")
    op.drop_index("ix_faucet_claims_agent", table_name="faucet_claims")
    op.drop_index("ix_faucet_claims_user", table_name="faucet_claims")
    op.drop_table("faucet_claims")

    op.drop_index("ux_ref_reward_dedupe", table_name="referral_reward_events")
    op.drop_index("ix_ref_reward_benef_agent", table_name="referral_reward_events")
    op.drop_index("ix_ref_reward_benef_user", table_name="referral_reward_events")
    op.drop_index("ix_ref_reward_attribution", table_name="referral_reward_events")
    op.drop_table("referral_reward_events")

    op.drop_index("ux_referral_attributions_referred_agent_unique", table_name="referral_attributions")
    op.drop_index("ux_referral_attributions_referred_user_unique", table_name="referral_attributions")
    op.drop_index("ix_referral_attributions_referred_agent", table_name="referral_attributions")
    op.drop_index("ix_referral_attributions_referred_user", table_name="referral_attributions")
    op.drop_index("ix_referral_attributions_code", table_name="referral_attributions")
    op.drop_table("referral_attributions")

    op.drop_index("ix_referral_codes_owner_agent", table_name="referral_codes")
    op.drop_index("ix_referral_codes_owner_user", table_name="referral_codes")
    op.drop_index("ux_referral_codes_code", table_name="referral_codes")
    op.drop_table("referral_codes")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
