"""Bind People + AI platform seeds to user 3n3rgy.

Revision ID: 089_economy_seed_owner
Revises: 088_project_economy
"""

from __future__ import annotations

import secrets
import uuid

import bcrypt
import sqlalchemy as sa
from alembic import op

revision = "089_economy_seed_owner"
down_revision = "088_project_economy"
branch_labels = None
depends_on = None

SEED_OWNER_EMAIL = "dragon.cat.trx@gmail.com"
SEED_OWNER_DISPLAY = "3n3rgy"
_SEED_KEY_SQL = "('aeterna', 'galaxy', 'lunar', 'stardust', 'starlink')"


def _unusable_password_hash() -> str:
    # Random secret is discarded — account cannot be logged into with a known password.
    secret = secrets.token_urlsafe(48).encode("utf-8")
    return bcrypt.hashpw(secret, bcrypt.gensalt()).decode("utf-8")


def upgrade() -> None:
    conn = op.get_bind()
    row = conn.execute(
        sa.text("SELECT id, display_name FROM users WHERE email = :email"),
        {"email": SEED_OWNER_EMAIL},
    ).fetchone()

    if row is None:
        user_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
                INSERT INTO users (id, email, password_hash, display_name, created_at)
                VALUES (:id, :email, :password_hash, :display_name, now())
                """
            ),
            {
                "id": user_id,
                "email": SEED_OWNER_EMAIL,
                "password_hash": _unusable_password_hash(),
                "display_name": SEED_OWNER_DISPLAY,
            },
        )
    else:
        user_id = str(row[0])
        if not (row[1] or "").strip():
            conn.execute(
                sa.text("UPDATE users SET display_name = :name WHERE id = :id"),
                {"name": SEED_OWNER_DISPLAY, "id": user_id},
            )

    conn.execute(
        sa.text(
            f"""
            UPDATE economy_projects
            SET owner_user_id = :owner_id, updated_at = now()
            WHERE is_platform_seed IS TRUE
              AND seed_key IN {_SEED_KEY_SQL}
            """
        ),
        {"owner_id": user_id},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            f"""
            UPDATE economy_projects
            SET owner_user_id = NULL, updated_at = now()
            WHERE is_platform_seed IS TRUE
              AND seed_key IN {_SEED_KEY_SQL}
            """
        )
    )
    # Do not delete the user — they may own other data.
