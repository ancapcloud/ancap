"""rop04: add reconciliation_status field to workflow_cost_evidence.

Revision ID: rop04_add_reconciliation_status
Revises: rop04_add_cost_evidence_fields
Create Date: 2026-11-02

This migration adds reconciliation_status field for ROP-04 (actual economics and renewal):
- reconciliation_status: tracks reconciliation state (pending/verified/failed)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rop04_add_reconciliation_status'
down_revision: Union[str, None] = 'rop04_add_cost_evidence_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reconciliation_status column to workflow_cost_evidence
    op.add_column('workflow_cost_evidence', sa.Column(
        'reconciliation_status', sa.String(32), nullable=True,
        server_default=None
    ))

    # Create index on reconciliation_status for faster lookups
    with op.batch_alter_table('workflow_cost_evidence') as batch_op:
        batch_op.create_index(
            'ix_workflow_cost_reconciliation_status',
            ['reconciliation_status'],
            unique=False,
            postgresql_using='btree'
        )


def downgrade() -> None:
    with op.batch_alter_table('workflow_cost_evidence') as batch_op:
        batch_op.drop_index('ix_workflow_cost_reconciliation_status')

    # Drop column
    op.drop_column('workflow_cost_evidence', 'reconciliation_status')
