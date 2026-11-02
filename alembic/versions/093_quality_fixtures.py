"""De-identified evaluation fixtures for ROP-03 quality testing."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "093_quality_fixtures"
down_revision = "093_research_operations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("quality_fixtures",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("fixture_type", sa.String(64), nullable=False, comment="type: price_change, markup_noise, unavailable_source, contradiction, malicious_instructions"),
        sa.Column("language", sa.String(10), nullable=False, comment="zh-Hant, en, ru, de, fr"),
        sa.Column("sample_id", sa.String(64), nullable=False, comment="unique sample identifier"),
        sa.Column("expected_result", sa.Text(), nullable=True, comment="expected OCR output or verdict"),
        sa.Column("actual_result", sa.Text(), nullable=True, comment="actual OCR output from model"),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True, comment="model confidence 0.0-1.0"),
        sa.Column("is_available", sa.Boolean(), nullable=False, default=True, comment="source availability status"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("fixture_type", "language", "sample_id", name="uq_quality_fixture_sample"),
    )


def downgrade():
    op.drop_table("quality_fixtures")
