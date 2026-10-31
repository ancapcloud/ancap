"""Migration 002: Add quality fixtures table for Research Operations P0."""

from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime


def upgrade():
    # Create quality_fixtures table (matching app.db.models.QualityFixture structure)
    op.create_table(
        'quality_fixtures',
        sa.Column('id', sa.Uuid(), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fixture_name', sa.String(255), nullable=False),
        sa.Column('fixture_type', sa.String(100), nullable=False),  # e.g., "address", "amount", "language"
        sa.Column('language', sa.String(10), nullable=True),  # zh-Hant, ru-RU, etc.
        sa.Column('test_cases', sa.JSON(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('accuracy_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),  # pending, running, completed, failed
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create indexes
    op.create_index('ix_quality_fixtures_fixture_name', 'quality_fixtures', ['fixture_name'])
    op.create_index('ix_quality_fixtures_status', 'quality_fixtures', ['status'])


def downgrade():
    op.drop_table('quality_fixtures')
