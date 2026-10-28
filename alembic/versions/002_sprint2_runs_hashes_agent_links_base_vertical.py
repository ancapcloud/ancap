"""Sprint-2: runs hashes, evaluations unique, agent_links, seed BaseVertical

Revision ID: 002
Revises: 001
Create Date: 2025-02-23

"""
from typing import Sequence, Union
import uuid
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("inputs_hash", sa.Text(), nullable=True))
    op.add_column("runs", sa.Column("workflow_hash", sa.Text(), nullable=True))
    op.add_column("runs", sa.Column("outputs_hash", sa.Text(), nullable=True))
    op.add_column("runs", sa.Column("proof_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_index("ix_evaluations_strategy_version_id", "evaluations", ["strategy_version_id"], unique=True)

    op.create_table(
        "agent_links",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("linked_agent_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("link_type", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["linked_agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_links_agent_id", "agent_links", ["agent_id"], unique=False)
    op.create_unique_constraint("uq_agent_links_pair", "agent_links", ["agent_id", "linked_agent_id"])

    # Seed BaseVertical
    vertical_id = str(uuid.uuid4())
    spec_id = str(uuid.uuid4())
    base_vertical_spec = {
        "allowed_actions": [
            {"name": "const", "args_schema": {"type": "object"}, "description": "Constant value"},
            {"name": "math_add", "args_schema": {"type": "object"}},
            {"name": "math_sub", "args_schema": {"type": "object"}},
            {"name": "math_mul", "args_schema": {"type": "object"}},
            {"name": "math_div", "args_schema": {"type": "object"}},
            {"name": "cmp", "args_schema": {"type": "object"}},
            {"name": "if", "args_schema": {"type": "object"}},
            {"name": "rand_uniform", "args_schema": {"type": "object"}},
            {"name": "portfolio_buy", "args_schema": {"type": "object"}},
            {"name": "portfolio_sell", "args_schema": {"type": "object"}},
        ],
        "required_resources": [],
        "metrics": [
            {"name": "pnl_amount", "value_schema": {"type": "number"}},
            {"name": "return_pct", "value_schema": {"type": "number"}},
            {"name": "max_drawdown_pct", "value_schema": {"type": "number"}},
            {"name": "steps_executed", "value_schema": {"type": "integer"}},
            {"name": "runtime_ms", "value_schema": {"type": "integer"}},
            {"name": "risk_breaches", "value_schema": {"type": "integer"}},
        ],
        "risk_spec": {"max_loss_pct": 0.1},
    }
    spec_json_escaped = json.dumps(base_vertical_spec).replace("'", "''")
    op.execute(
        f"INSERT INTO verticals (id, name, status, owner_agent_id, created_at) "
        f"VALUES ('{vertical_id}', 'BaseVertical', 'active', NULL, NOW())"
    )
    op.execute(
        f"INSERT INTO vertical_specs (id, vertical_id, spec_json, created_at) "
        f"VALUES ('{spec_id}', '{vertical_id}', '{spec_json_escaped}'::jsonb, NOW())"
    )


def downgrade() -> None:
    op.drop_constraint("uq_agent_links_pair", "agent_links", type_="unique")
    op.drop_index("ix_agent_links_agent_id", "agent_links")
    op.drop_table("agent_links")
    op.drop_index("ix_evaluations_strategy_version_id", "evaluations")
    op.drop_column("runs", "proof_json")
    op.drop_column("runs", "outputs_hash")
    op.drop_column("runs", "workflow_hash")
    op.drop_column("runs", "inputs_hash")
    op.execute("DELETE FROM vertical_specs WHERE vertical_id IN (SELECT id FROM verticals WHERE name = 'BaseVertical')")
    op.execute("DELETE FROM verticals WHERE name = 'BaseVertical'")

# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
