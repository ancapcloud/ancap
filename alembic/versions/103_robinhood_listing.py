from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "103_robinhood_listing"
down_revision = "102_cost_evidence_attribution"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "robinhood_listings",
        sa.Column(
            "run_id",
            UUID(),
            sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(42), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("packet", JSONB(), nullable=False),
        sa.Column("contact", sa.String(320), nullable=False),
        sa.Column("comment", sa.Text()),
    )
    op.create_index(
        "uq_robinhood_published",
        "robinhood_listings",
        ["chain_id", "address"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
    )


def downgrade():
    op.drop_table("robinhood_listings")
