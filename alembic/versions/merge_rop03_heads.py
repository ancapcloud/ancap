"""No-op ROP-03 revision kept on the 098 branch.

History note: this revision was originally intended to merge
``098_merge_release_heads`` with the quality-fixtures branch, but it only
received ``098_merge_release_heads`` as a parent. It is retained unchanged
(down_revision) because it may already be stamped in deployed databases; the
single-head merge for the whole graph is ``100_merge_release_heads``.

Revision ID: merge_rop03_heads
Revises: 098_merge_release_heads
Create Date: 2026-11-02

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'merge_rop03_heads'
down_revision: Union[str, Sequence[str], None] = ('098_merge_release_heads',)
branch_labels: Union[str, Sequence[None], None] = None
depends_on: Union[str, Sequence[None], None] = None


def upgrade() -> None:
    # No schema changes: the migration only marks the branch as applied.
    pass


def downgrade() -> None:
    # No schema changes to undo. ``op.merge`` is not an Alembic operation; the
    # previous implementation raised AttributeError on downgrade.
    pass
