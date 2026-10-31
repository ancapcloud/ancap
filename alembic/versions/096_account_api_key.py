"""One platform API key per user, revocation and request statistics."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "096_account_api_key"
down_revision = "a72e12eb9246"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("api_keys", sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), nullable=True))
    op.create_foreign_key("fk_api_keys_owner_user", "api_keys", "users", ["owner_user_id"], ["id"], ondelete="CASCADE")
    op.create_unique_constraint("uq_api_keys_owner_user_id", "api_keys", ["owner_user_id"])
    for name in ("revoked_at", "last_used_at"):
        op.add_column("api_keys", sa.Column(name, sa.DateTime(timezone=True), nullable=True))
    for name in ("request_count", "success_count", "error_count"):
        op.add_column("api_keys", sa.Column(name, sa.BigInteger(), nullable=False, server_default="0"))


def downgrade():
    for name in ("error_count", "success_count", "request_count", "last_used_at", "revoked_at"):
        op.drop_column("api_keys", name)
    op.drop_constraint("uq_api_keys_owner_user_id", "api_keys", type_="unique")
    op.drop_constraint("fk_api_keys_owner_user", "api_keys", type_="foreignkey")
    op.drop_column("api_keys", "owner_user_id")
