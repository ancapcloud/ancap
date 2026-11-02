"""Align onboarding_templates with the ORM model.

``70cb1adb8f05`` was created as a separate Alembic root and its autogenerate
captured columns without server defaults, a JSON (not JSONB) ``config_json``
and no foreign key. New inserts therefore failed with a NOT NULL violation on
``created_at``. This revision brings existing databases in line with
``app.db.models.OnboardingTemplate`` without rewriting the already-applied
migration.

Revision ID: 101_onboarding_templates_fix
Revises: 100_merge_release_heads
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "101_onboarding_templates_fix"
down_revision: Union[str, Sequence[str], None] = "100_merge_release_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_created_by_fk(bind) -> bool:
    inspector = sa.inspect(bind)
    return any(
        fk.get("name") == "fk_onboarding_templates_created_by_user"
        for fk in inspector.get_foreign_keys("onboarding_templates")
    )


def upgrade() -> None:
    op.alter_column(
        "onboarding_templates",
        "created_at",
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    op.alter_column(
        "onboarding_templates",
        "updated_at",
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    op.alter_column(
        "onboarding_templates",
        "config_json",
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="config_json::jsonb",
    )
    bind = op.get_bind()
    if not _has_created_by_fk(bind):
        op.create_foreign_key(
            "fk_onboarding_templates_created_by_user",
            "onboarding_templates",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_created_by_fk(bind):
        op.drop_constraint(
            "fk_onboarding_templates_created_by_user",
            "onboarding_templates",
            type_="foreignkey",
        )
    op.alter_column(
        "onboarding_templates",
        "config_json",
        type_=sa.JSON(),
        postgresql_using="config_json::json",
    )
    op.alter_column("onboarding_templates", "created_at", server_default=None)
    op.alter_column("onboarding_templates", "updated_at", server_default=None)
