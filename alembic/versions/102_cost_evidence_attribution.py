"""Add COST-05 attribution_data to workflow_cost_evidence.

The ORM model gained ``attribution_data`` for category-level cost attribution;
without a migration a fresh database cannot select ``WorkflowCostEvidence``.

Revision ID: 102_cost_evidence_attribution
Revises: 101_onboarding_templates_fix
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "102_cost_evidence_attribution"
down_revision: Union[str, Sequence[str], None] = "101_onboarding_templates_fix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(bind) -> set[str]:
    return {column["name"] for column in sa.inspect(bind).get_columns("workflow_cost_evidence")}


def upgrade() -> None:
    if "attribution_data" not in _columns(op.get_bind()):
        op.add_column(
            "workflow_cost_evidence",
            sa.Column(
                "attribution_data",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )


def downgrade() -> None:
    if "attribution_data" in _columns(op.get_bind()):
        op.drop_column("workflow_cost_evidence", "attribution_data")
