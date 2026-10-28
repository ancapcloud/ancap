"""Contracts and Run.contract_id.

Revision ID: 023
Revises: 022
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("employer_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("worker_agent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_ref_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "proposed",
                "active",
                "paused",
                "completed",
                "cancelled",
                "disputed",
                name="contractstatusenum",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "payment_model",
            sa.Enum("fixed", "per_run", name="paymentmodelenum"),
            nullable=False,
        ),
        sa.Column("fixed_amount_value", sa.Numeric(36, 18), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="VUSD"),
        sa.Column("max_runs", sa.Integer(), nullable=True),
        sa.Column("risk_policy_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("risk_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_from_order_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_contracts_employer_agent_id", "contracts", ["employer_agent_id"])
    op.create_index("ix_contracts_worker_agent_id", "contracts", ["worker_agent_id"])
    op.create_index("ix_contracts_status", "contracts", ["status"])
    op.create_index("ix_contracts_scope_ref_id", "contracts", ["scope_ref_id"])

    op.add_column(
        "runs",
        sa.Column(
            "contract_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("contracts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("runs", "contract_id")
    op.drop_index("ix_contracts_scope_ref_id", table_name="contracts")
    op.drop_index("ix_contracts_status", table_name="contracts")
    op.drop_index("ix_contracts_worker_agent_id", table_name="contracts")
    op.drop_index("ix_contracts_employer_agent_id", table_name="contracts")
    op.drop_table("contracts")
    op.execute("DROP TYPE IF EXISTS contractstatusenum")
    op.execute("DROP TYPE IF EXISTS paymentmodelenum")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
