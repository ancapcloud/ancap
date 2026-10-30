"""add workflow_cost_allocations table for cost attribution

Revision ID: 092_add_workflow_cost_allocations
Revises: b57ee693ac56
Create Date: 2026-10-29 22:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '092_add_workflow_cost_allocations'
down_revision: Union[str, None] = 'b57ee693ac56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflow_cost_allocations table for cost attribution across workflow runs
    op.create_table(
        'workflow_cost_allocations',
        sa.Column('evidence_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_run_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.PrimaryKeyConstraint('evidence_id', 'workflow_run_id'),
        sa.CheckConstraint('amount >= 0 AND amount != \'NaN\'::numeric', name='ck_workflow_cost_allocation_amount')
    )

    # Create index on workflow_run_id for efficient lookups
    op.create_index(
        op.f('ix_workflow_cost_allocations_workflow_run_id'),
        'workflow_cost_allocations', ['workflow_run_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index(
        op.f('ix_workflow_cost_allocations_workflow_run_id'),
        table_name='workflow_cost_allocations'
    )

    # Drop table
    op.drop_table('workflow_cost_allocations')
