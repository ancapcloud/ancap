"""Merge the five release heads into a single Alembic head.

Before this revision the graph had five heads:

* ``093_quality_fixtures`` — ROP-03 quality fixtures;
* ``099_source_schedules`` — ROP-03 bounded collection;
* ``70cb1adb8f05`` — onboarding templates (created as a second root,
  ``down_revision = None``);
* ``merge_rop03_heads`` — no-op revision on the 098 branch;
* ``rop04_add_reconciliation_status`` — ROP-04 cost evidence.

Merging (rather than rewriting existing parents) keeps already stamped
databases valid: Alembic simply marks this revision as applied after all five
branches are present.

Revision ID: 100_merge_release_heads
Revises: 093_quality_fixtures, 099_source_schedules, 70cb1adb8f05,
         merge_rop03_heads, rop04_add_reconciliation_status
Create Date: 2026-11-02
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "100_merge_release_heads"
down_revision: Union[str, Sequence[str], None] = (
    "093_quality_fixtures",
    "099_source_schedules",
    "70cb1adb8f05",
    "merge_rop03_heads",
    "rop04_add_reconciliation_status",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge-only revision: every branch keeps its own schema changes.
    pass


def downgrade() -> None:
    # Un-merging is handled by Alembic; there is no schema change to undo.
    pass
