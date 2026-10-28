"""Contract milestones and Run.contract_milestone_id.

Revision ID: 028
Revises: 027
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contract_milestones",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "contract_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("contracts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "active",
                "submitted",
                "accepted",
                "rejected",
                "paid",
                "cancelled",
                name="contractmilestonestatusenum",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("amount_value", sa.Numeric(36, 18), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="VUSD"),
        sa.Column("required_runs", sa.Integer(), nullable=True),
        sa.Column("completed_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_contract_milestones_contract_id", "contract_milestones", ["contract_id"])
    op.create_index("ix_contract_milestones_status", "contract_milestones", ["status"])
    op.create_index("ix_contract_milestones_contract_order", "contract_milestones", ["contract_id", "order_index"])
    op.create_index("ix_contract_milestones_contract_status", "contract_milestones", ["contract_id", "status"])
    op.create_index("ix_contract_milestones_contract_created", "contract_milestones", ["contract_id", "created_at"])

    op.add_column(
        "runs",
        sa.Column(
            "contract_milestone_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("contract_milestones.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_runs_contract_milestone_id", "runs", ["contract_milestone_id"])


def downgrade() -> None:
    op.drop_index("ix_runs_contract_milestone_id", table_name="runs")
    op.drop_column("runs", "contract_milestone_id")

    op.drop_index("ix_contract_milestones_contract_created", table_name="contract_milestones")
    op.drop_index("ix_contract_milestones_contract_status", table_name="contract_milestones")
    op.drop_index("ix_contract_milestones_contract_order", table_name="contract_milestones")
    op.drop_index("ix_contract_milestones_status", table_name="contract_milestones")
    op.drop_index("ix_contract_milestones_contract_id", table_name="contract_milestones")
    op.drop_table("contract_milestones")
    op.execute("DROP TYPE IF EXISTS contractmilestonestatusenum")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
