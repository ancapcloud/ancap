"""Add quality fixtures / unknown expenses; keep cost allocation columns idempotent

Revision ID: 30fbd2048486
Revises: 096_account_api_key
Create Date: 2026-10-31 22:57:14.922936

a72e12eb9246 already created costcategoryenum and the workflow_cost_allocations
source columns. This revision must not recreate them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "30fbd2048486"
down_revision: Union[str, None] = "096_account_api_key"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COST_CATEGORY = postgresql.ENUM(
    "model",
    "data",
    "infrastructure",
    "review",
    "support",
    "payment_fee",
    "creator_payout",
    name="costcategoryenum",
    create_type=False,
)


def _has_table(bind, name: str) -> bool:
    return sa.inspect(bind).has_table(name)


def _has_column(bind, table: str, column: str) -> bool:
    if not _has_table(bind, table):
        return False
    return column in {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    _COST_CATEGORY.create(bind, checkfirst=True)

    if not _has_table(bind, "quality_fixtures"):
        op.create_table(
            "quality_fixtures",
            sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
            sa.Column(
                "fixture_type",
                sa.String(length=64),
                nullable=False,
                comment="type: price_change, markup_noise, unavailable_source, contradiction, malicious_instructions",
            ),
            sa.Column("language", sa.String(length=10), nullable=False, comment="zh-Hant, en, ru, de, fr"),
            sa.Column("sample_id", sa.String(length=64), nullable=False, comment="unique sample identifier"),
            sa.Column("expected_result", sa.Text(), nullable=True, comment="expected OCR output or verdict"),
            sa.Column("actual_result", sa.Text(), nullable=True, comment="actual OCR output from model"),
            sa.Column(
                "confidence_score",
                sa.Numeric(precision=5, scale=2),
                nullable=True,
                comment="model confidence 0.0-1.0",
            ),
            sa.Column("is_available", sa.Boolean(), nullable=False, comment="source availability status"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("fixture_type", "language", "sample_id", name="uq_quality_fixture_sample"),
        )

    if not _has_table(bind, "unknown_expense_records"):
        op.create_table(
            "unknown_expense_records",
            sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
            sa.Column("client_id", sa.String(length=255), nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False),
            sa.Column("amount", sa.Numeric(precision=36, scale=18), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=True),
            sa.Column("provider_name", sa.String(length=255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("source_reference", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("recorded_by_user_id", sa.UUID(as_uuid=False), nullable=True),
            sa.CheckConstraint("amount >= 0 AND amount != 'NaN'::numeric", name="ck_unknown_expense_amount"),
            sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_unknown_expense_client_period",
            "unknown_expense_records",
            ["client_id", "period_start", "period_end"],
            unique=False,
        )
        op.create_index(
            op.f("ix_unknown_expense_records_client_id"),
            "unknown_expense_records",
            ["client_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_unknown_expense_records_period_end"),
            "unknown_expense_records",
            ["period_end"],
            unique=False,
        )
        op.create_index(
            op.f("ix_unknown_expense_records_period_start"),
            "unknown_expense_records",
            ["period_start"],
            unique=False,
        )

    if not _has_column(bind, "workflow_cost_allocations", "evidence_line_id"):
        op.add_column(
            "workflow_cost_allocations",
            sa.Column("evidence_line_id", sa.String(length=255), nullable=True),
        )
    if not _has_column(bind, "workflow_cost_allocations", "evidence_amount"):
        op.add_column(
            "workflow_cost_allocations",
            sa.Column("evidence_amount", sa.Numeric(precision=36, scale=18), nullable=True),
        )
    if not _has_column(bind, "workflow_cost_allocations", "category"):
        op.add_column(
            "workflow_cost_allocations",
            sa.Column("category", _COST_CATEGORY, nullable=True),
        )
    if not _has_column(bind, "workflow_cost_allocations", "currency"):
        op.add_column(
            "workflow_cost_allocations",
            sa.Column("currency", sa.String(length=3), nullable=True),
        )

    for col in ("author", "distributions", "allocations", "verification_basis", "source_url"):
        if _has_column(bind, "workflow_cost_evidence", col):
            op.drop_column("workflow_cost_evidence", col)


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "workflow_cost_evidence", "source_url"):
        op.add_column(
            "workflow_cost_evidence",
            sa.Column("source_url", sa.VARCHAR(length=512), autoincrement=False, nullable=True),
        )
    if not _has_column(bind, "workflow_cost_evidence", "verification_basis"):
        op.add_column(
            "workflow_cost_evidence",
            sa.Column("verification_basis", sa.VARCHAR(length=32), autoincrement=False, nullable=False),
        )
    if not _has_column(bind, "workflow_cost_evidence", "allocations"):
        op.add_column(
            "workflow_cost_evidence",
            sa.Column("allocations", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
        )
    if not _has_column(bind, "workflow_cost_evidence", "distributions"):
        op.add_column(
            "workflow_cost_evidence",
            sa.Column("distributions", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
        )
    if not _has_column(bind, "workflow_cost_evidence", "author"):
        op.add_column(
            "workflow_cost_evidence",
            sa.Column("author", sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        )

    # Do not drop allocation columns added by a72e12eb9246.
    if _has_table(bind, "unknown_expense_records"):
        op.drop_index(op.f("ix_unknown_expense_records_period_start"), table_name="unknown_expense_records")
        op.drop_index(op.f("ix_unknown_expense_records_period_end"), table_name="unknown_expense_records")
        op.drop_index(op.f("ix_unknown_expense_records_client_id"), table_name="unknown_expense_records")
        op.drop_index("ix_unknown_expense_client_period", table_name="unknown_expense_records")
        op.drop_table("unknown_expense_records")
    if _has_table(bind, "quality_fixtures"):
        op.drop_table("quality_fixtures")
