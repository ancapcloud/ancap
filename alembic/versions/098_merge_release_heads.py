"""Merge source quotas and provider cost evidence release branches.

Revision ID: 098_merge_release_heads
Revises: 097_source_quotas, rop04_add_cost_evidence_fields
"""
revision = "098_merge_release_heads"
down_revision = ("097_source_quotas", "rop04_add_cost_evidence_fields")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
