"""Merge packet-template and Robinhood-listing migration branches.

Both revisions extend 102 independently; retain both applied histories.
"""
revision = "104_merge_packet_listing"
down_revision = ("103_packet_templates_rop05", "103_robinhood_listing")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
