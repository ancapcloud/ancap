"""People + AI project economy tables + platform seed projects.

Revision ID: 088_project_economy
Revises: 087_workflow_operations
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "088_project_economy"
down_revision = "087_workflow_operations"
branch_labels = None
depends_on = None

SEED_PROJECTS = (
    (
        "11111111-1111-4111-8111-111111111101",
        "aeterna",
        "aeterna-longevity-brief",
        "AETERNA — longevity research brief",
        "Turn a broad interest in longevity research into a clear brief for a qualified professional.",
        "A research outline, evidence checklist and professional-review questions.",
        "Illustrative digital brief only — no medical service or patient work.",
        "demo",
        "/aeterna",
        "Draft longevity research questions",
        "Sources dated, limitations listed, no individual health assessment claimed.",
        "11111111-1111-4111-8111-211111111101",
    ),
    (
        "11111111-1111-4111-8111-111111111102",
        "galaxy",
        "galaxy-edge-infra-concept",
        "Galaxy — encrypted edge infrastructure concept",
        "Sketch an encrypted edge-computing concept for a hypothetical space project.",
        "An architecture brief and checks for a potential infrastructure partner.",
        "Concept brief only — no orbital deployment or supplier agreement.",
        "concept",
        "/galaxy",
        "Map trust boundaries and open questions",
        "Each trust boundary identifiable; hosting and key custody questions listed.",
        "11111111-1111-4111-8111-211111111102",
    ),
    (
        "11111111-1111-4111-8111-111111111103",
        "lunar",
        "lunar-catalog-card",
        "Lunar — science catalog card sample",
        "Design a science-themed catalog using fictional lunar parcel records.",
        "A sample catalog specification with a clearly labeled fictional entry.",
        "Educational catalog sample — no land title or mining rights.",
        "demo",
        "/lunar",
        "Propose catalog record schema",
        "Fictional entry labeled; ownership claims explicitly excluded.",
        "11111111-1111-4111-8111-211111111103",
    ),
    (
        "11111111-1111-4111-8111-111111111104",
        "stardust",
        "stardust-weather-brief",
        "Stardust — weather observation brief",
        "Define a weather-research dashboard with sample observations and human review.",
        "A dashboard brief, input schema and sample review note.",
        "Dashboard example — not a live forecast or emergency alert.",
        "demo",
        "/stardust",
        "Structure observation review fields",
        "Missing source/timestamp flagged; human verification status required.",
        "11111111-1111-4111-8111-211111111104",
    ),
    (
        "11111111-1111-4111-8111-111111111105",
        "starlink",
        "starlink-install-intake",
        "Starlink — installation intake for independent technician",
        "Prepare a sample satellite-internet installation request for an independent technician.",
        "A site-intake brief and questions before a service quote.",
        "Intake sample only — does not book installation or claim Starlink partnership.",
        "concept",
        "/starlink-install",
        "Collect site intake checklist",
        "Location, mount, power, cable route and access permission fields present.",
        "11111111-1111-4111-8111-211111111105",
    ),
)


def upgrade() -> None:
    op.create_table(
        "economy_projects",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("result_promise", sa.Text(), nullable=False),
        sa.Column("earning_model", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
        sa.Column("kind", sa.String(length=24), nullable=False, server_default="community"),
        sa.Column("seed_key", sa.String(length=40), nullable=True),
        sa.Column("is_platform_seed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("background_href", sa.String(length=200), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_economy_projects_owner_user_id", "economy_projects", ["owner_user_id"])
    op.create_index("ix_economy_projects_slug", "economy_projects", ["slug"], unique=True)
    op.create_index("ix_economy_projects_status", "economy_projects", ["status"])
    op.create_index("ix_economy_projects_seed_key", "economy_projects", ["seed_key"], unique=True)

    op.create_table(
        "economy_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("economy_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("acceptance_criteria", sa.Text(), nullable=False),
        sa.Column("stage_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price_acp", sa.Numeric(36, 18), nullable=True),
        sa.Column("assignee_type", sa.String(length=16), nullable=False, server_default="human"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_economy_tasks_project_id", "economy_tasks", ["project_id"])

    op.create_table(
        "economy_applications",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("economy_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("applicant_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_economy_applications_task_id", "economy_applications", ["task_id"])
    op.create_index("ix_economy_applications_applicant_user_id", "economy_applications", ["applicant_user_id"])
    op.create_index(
        "ix_economy_applications_task_user",
        "economy_applications",
        ["task_id", "applicant_user_id"],
        unique=True,
    )

    projects = sa.table(
        "economy_projects",
        sa.column("id", postgresql.UUID(as_uuid=False)),
        sa.column("owner_user_id", postgresql.UUID(as_uuid=False)),
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
        sa.column("summary", sa.Text),
        sa.column("result_promise", sa.Text),
        sa.column("earning_model", sa.Text),
        sa.column("status", sa.String),
        sa.column("kind", sa.String),
        sa.column("seed_key", sa.String),
        sa.column("is_platform_seed", sa.Boolean),
        sa.column("background_href", sa.String),
        sa.column("metadata_json", postgresql.JSONB),
    )
    tasks = sa.table(
        "economy_tasks",
        sa.column("id", postgresql.UUID(as_uuid=False)),
        sa.column("project_id", postgresql.UUID(as_uuid=False)),
        sa.column("title", sa.String),
        sa.column("acceptance_criteria", sa.Text),
        sa.column("stage_order", sa.Integer),
        sa.column("assignee_type", sa.String),
    )

    for order, row in enumerate(SEED_PROJECTS, start=1):
        (
            project_id,
            seed_key,
            slug,
            title,
            summary,
            result_promise,
            earning_model,
            kind,
            background_href,
            task_title,
            acceptance,
            task_id,
        ) = row
        op.bulk_insert(
            projects,
            [
                {
                    "id": project_id,
                    "owner_user_id": None,
                    "slug": slug,
                    "title": title,
                    "summary": summary,
                    "result_promise": result_promise,
                    "earning_model": earning_model,
                    "status": "published",
                    "kind": kind,
                    "seed_key": seed_key,
                    "is_platform_seed": True,
                    "background_href": background_href,
                    "metadata_json": {
                        "ai_authored": True,
                        "platform_order": order,
                        "disclosure": "AI-created demo project — not a completed customer order.",
                    },
                }
            ],
        )
        op.bulk_insert(
            tasks,
            [
                {
                    "id": task_id,
                    "project_id": project_id,
                    "title": task_title,
                    "acceptance_criteria": acceptance,
                    "stage_order": 1,
                    "assignee_type": "human",
                }
            ],
        )


def downgrade() -> None:
    op.drop_index("ix_economy_applications_task_user", table_name="economy_applications")
    op.drop_index("ix_economy_applications_applicant_user_id", table_name="economy_applications")
    op.drop_index("ix_economy_applications_task_id", table_name="economy_applications")
    op.drop_table("economy_applications")
    op.drop_index("ix_economy_tasks_project_id", table_name="economy_tasks")
    op.drop_table("economy_tasks")
    op.drop_index("ix_economy_projects_seed_key", table_name="economy_projects")
    op.drop_index("ix_economy_projects_status", table_name="economy_projects")
    op.drop_index("ix_economy_projects_slug", table_name="economy_projects")
    op.drop_index("ix_economy_projects_owner_user_id", table_name="economy_projects")
    op.drop_table("economy_projects")
