"""feat(rop-05): add onboarding templates table

Revision ID: ce103b55b383
Revises: 102_cost_evidence_attribution
Create Date: 2026-11-02 15:52:25.470204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce103b55b383'
down_revision: Union[str, None] = '102_cost_evidence_attribution'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create onboarding_templates table
    op.create_table('onboarding_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.UUID(), nullable=True),
        sa.Column('template_type', sa.Enum('general', 'crypto', 'social', 'news', name='template_type_enum'), nullable=False, default='general'),
        sa.Column('source_categories', sa.JSONB(), nullable=True),
        sa.Column('packet_template', sa.JSONB(), nullable=True),
        sa.Column('config_json', sa.JSONB(), nullable=True),
        sa.Column('validation_config', sa.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_onboarding_template_name')
    )
    
    # Create index on created_by_user_id
    op.create_index(op.f('ix_onboarding_templates_created_by_user_id'), 'onboarding_templates', 'created_by_user_id')
    op.create_index(op.f('ix_onboarding_templates_name'), 'onboarding_templates', 'name')


def downgrade() -> None:
    op.drop_table('onboarding_templates')
