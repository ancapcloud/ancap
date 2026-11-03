"""ROP-03: Add quality fixtures table for de-identified evaluation samples.

Revision ID: 093_quality_fixtures
Revises: merge_rop03_heads
Create Date: 2026-11-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '093_quality_fixtures'
down_revision: Union[str, Sequence[str], None] = ('merge_rop03_heads',)
branch_labels: Union[str, Sequence[None], None] = None
depends_on: Union[str, Sequence[None], None] = None


def upgrade() -> None:
    # Create quality_fixtures table for de-identified evaluation fixtures
    op.create_table(
        'quality_fixtures',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('fixture_type', sa.String(64), nullable=False, comment='type: price_change, markup_noise, unavailable_source, contradiction, malicious_instructions'),
        sa.Column('language', sa.String(10), nullable=False, comment='zh-Hant, en, ru, de, fr'),
        sa.Column('sample_id', sa.String(64), nullable=False, comment='unique sample identifier'),
        sa.Column('expected_result', sa.Text(), nullable=True, comment='expected OCR output or classification'),
        sa.Column('actual_result', sa.Text(), nullable=True, comment='actual OCR output or classification'),
        sa.Column('confidence_score', sa.Float(), nullable=True, comment='model confidence 0.0-1.0'),
        sa.Column('is_available', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    # Create index on language and fixture_type for efficient filtering
    op.create_index('ix_quality_fixtures_language_fixture_type', 'quality_fixtures', ['language', 'fixture_type'])


def downgrade() -> None:
    op.drop_table('quality_fixtures')
