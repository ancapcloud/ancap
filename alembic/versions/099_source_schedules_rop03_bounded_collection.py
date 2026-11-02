"""add source schedules table for bounded collection (ROP-03)

Revision ID: 099_source_schedules
Revises: 098_merge_release_heads
Create Date: 2026-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '099_source_schedules'
down_revision = '098_merge_release_heads'
branch_labels = None
depends_on = None


def upgrade():
    # Create source_schedules table for ROP-03 bounded collection
    op.create_table('source_schedules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.String(255), nullable=False),
    sa.Column('source_type', sa.String(100), nullable=False),
    sa.Column('source_pattern', sa.String(512), nullable=True),
    sa.Column('check_interval_minutes', sa.Integer(), nullable=False),
    sa.Column('retention_days', sa.Integer(), nullable=False),
    sa.Column('max_sources', sa.Integer(), nullable=False),
    sa.Column('max_snapshots_per_source', sa.Integer(), nullable=False),
    sa.Column('max_claims_per_source', sa.Integer(), nullable=False),
    sa.Column('check_cooldown_seconds', sa.Integer(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.Index('ix_source_schedules_project_type', 'project_id', 'source_type')
    )
    
    # Add check constraints
    op.create_check_constraint(
        'ck_schedule_interval',
        'source_schedules',
        '(check_interval_minutes >= 1 and check_interval_minutes <= 1440)'
    )
    op.create_check_constraint(
        'ck_schedule_retention',
        'source_schedules',
        '(retention_days >= 1 and retention_days <= 365)'
    )


def downgrade():
    op.drop_constraint('ck_schedule_retention', 'source_schedules', type_='check')
    op.drop_constraint('ck_schedule_interval', 'source_schedules', type_='check')
    op.drop_index('ix_source_schedules_project_type', table_name='source_schedules')
    op.drop_table('source_schedules')
