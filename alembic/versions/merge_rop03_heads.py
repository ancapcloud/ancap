"""Merge ROP-03 heads into main branch

Revision ID: merge_rop03_heads
Revises: 098_merge_release_heads, rop03_quality_fixtures
Create Date: 2026-11-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_rop03_heads'
down_revision: Union[str, Sequence[str], None] = ('098_merge_release_heads',)
branch_labels: Union[str, Sequence[None], None] = None
depends_on: Union[str, Sequence[None], None] = None


def upgrade() -> None:
    # This is a merge migration - no schema changes needed
    # The quality_fixtures table was already created in rop03_quality_fixtures
    pass


def downgrade() -> None:
    # Downgrade to the previous heads
    op.merge(branch='rop03_quality_fixtures')
