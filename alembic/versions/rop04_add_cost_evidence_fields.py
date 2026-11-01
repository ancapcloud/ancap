"""rop04: add cost evidence fields for provider reconciliation and external events.

Revision ID: rop04_add_cost_evidence_fields
Revises: 092_workflow_cost_evidence
Create Date: 2026-11-01

This migration adds fields to support ROP-04 (actual economics and renewal):
- provider_id: for provider/document reconciliation
- document_type: to distinguish different document types
- external_payment_event: boolean flag for external payment events
- delivery_event: boolean flag for delivery events
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rop04_add_cost_evidence_fields'
down_revision: Union[str, None] = '092_workflow_cost_evidence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add provider_id column to workflow_cost_evidence
    op.add_column('workflow_cost_evidence', sa.Column(
        'provider_id', sa.String(128), nullable=True,
        server_default=None
    ))

    # Add document_type column to workflow_cost_evidence
    op.add_column('workflow_cost_evidence', sa.Column(
        'document_type', sa.String(64), nullable=True,
        server_default=None
    ))

    # Add external_payment_event column to workflow_cost_evidence
    op.add_column('workflow_cost_evidence', sa.Column(
        'external_payment_event', sa.Boolean(), nullable=True,
        server_default=False
    ))

    # Add delivery_event column to workflow_cost_evidence
    op.add_column('workflow_cost_evidence', sa.Column(
        'delivery_event', sa.Boolean(), nullable=True,
        server_default=False
    ))

    # Create index on provider_id for faster lookups
    with op.batch_alter_table('workflow_cost_evidence') as batch_op:
        batch_op.create_index(
            'ix_workflow_cost_provider_id',
            ['provider_id'],
            unique=False,
            postgresql_using='btree'
        )


def downgrade() -> None:
    with op.batch_alter_table('workflow_cost_evidence') as batch_op:
        batch_op.drop_index('ix_workflow_cost_provider_id')

    # Drop columns in reverse order of creation
    op.drop_column('workflow_cost_evidence', 'delivery_event')
    op.drop_column('workflow_cost_evidence', 'external_payment_event')
    op.drop_column('workflow_cost_evidence', 'document_type')
    op.drop_column('workflow_cost_evidence', 'provider_id')
