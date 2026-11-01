"""add_onboarding_templates_table

Revision ID: 70cb1adb8f05
Revises: 098_merge_release_heads
Create Date: 2026-11-01 15:39:56.937778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70cb1adb8f05'
down_revision: Union[str, None] = '098_merge_release_heads'
branch_labels: Union[str, Sequence[None], None] = None
depends_on: Union[str, Sequence[None], None] = None


def upgrade() -> None:
    # Create onboarding_templates table with correct schema matching models.py
    op.create_table('onboarding_templates',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(100), nullable=False),  # e.g., "quickstart", "faucet", "starter-pack"
        sa.Column('config_json', sa.JSON(), nullable=True),
        sa.Column('created_by_user_id', sa.UUID(as_uuid=True), nullable=True),  # FK to users.id
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # Add indexes
    op.create_index('ix_onboarding_templates_type', 'onboarding_templates', ['template_type'])
    op.create_index('ix_onboarding_templates_created_by', 'onboarding_templates', ['created_by_user_id'])


def downgrade() -> None:
    op.drop_table('onboarding_templates')
