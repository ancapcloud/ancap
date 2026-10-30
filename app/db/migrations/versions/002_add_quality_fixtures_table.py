"""add quality fixtures table

Revision ID: 002
Revises: cc78727d
Create Date: 2026-10-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = 'cc78727d'
branch_labels = None
depends_on = None


def upgrade():
    # Create quality_fixtures table
    op.create_table(
        'quality_fixtures',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('fixture_name', sa.String(128), nullable=False),
        sa.Column('fixture_type', sa.String(64), nullable=False),
        sa.Column('version', sa.String(32), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('test_cases', sa.JSONB(), nullable=True),
        sa.Column('expected_results', sa.JSONB(), nullable=True),
        sa.Column('actual_results', sa.JSONB(), nullable=True),
        sa.Column('source', sa.String(128), nullable=True),
        sa.Column('created_by', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fixture_name', name='uq_quality_fixtures_fixture_name'),
        sa.Index('ix_quality_fixtures_fixture_type', 'fixture_type'),
        sa.CheckConstraint("status IN ('active', 'deprecated', 'archived')", name='ck_quality_fixture_status')
    )


def downgrade():
    op.drop_table('quality_fixtures')
