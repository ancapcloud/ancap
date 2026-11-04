"""renewal_events: ROP-04 subscription/license renewal events

Revision ID: 099
Revises: d6891216
Create Date: 2026-11-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '099'
down_revision: Union[str, None] = '098_merge_release_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create renewal_events table
    op.create_table('renewal_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('project_id', sa.String(255), nullable=False),
    sa.Column('client_id', sa.String(255), nullable=False),
    sa.Column('subscription_id', sa.String(255), nullable=True),
    sa.Column('renewal_type', sa.String(50), nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actual_renewal_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('amount_due', sa.Numeric(12, 2), nullable=False),
    sa.Column('currency', sa.String(3), nullable=False),
    sa.Column('status', sa.String(50), nullable=False),
    sa.Column('payment_intent_id', sa.String(255), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.Index('ix_renewal_events_project_client', 'project_id', 'client_id'),
    sa.Index('ix_renewal_events_due_date', 'due_date'),
    sa.CheckConstraint("status IN ('pending', 'paid', 'failed', 'cancelled')", name='ck_renewal_status'),
    )


def downgrade() -> None:
    op.drop_table('renewal_events')
