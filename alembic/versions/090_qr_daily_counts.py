"""Persistent aggregate QR campaign counters."""
from alembic import op
import sqlalchemy as sa

revision = "090_qr_daily_counts"
down_revision = "089_economy_seed_owner"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("qr_daily_counts",
        sa.Column("campaign", sa.String(40), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("visits", sa.BigInteger(), nullable=False, server_default="0"))

def downgrade():
    op.drop_table("qr_daily_counts")
