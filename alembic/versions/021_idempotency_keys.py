"""Idempotency keys store for POST endpoints.

Revision ID: 021
Revises: 020
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_json", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("uq_idempotency_scope_key", "idempotency_keys", ["scope", "key"], unique=True)
    op.create_index("ix_idempotency_scope", "idempotency_keys", ["scope"])


def downgrade() -> None:
    op.drop_index("ix_idempotency_scope", table_name="idempotency_keys")
    op.drop_index("uq_idempotency_scope_key", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")


# Alembic loads these names as the migration module public interface.
__all__ = ["revision", "down_revision", "branch_labels", "depends_on", "upgrade", "downgrade"]
