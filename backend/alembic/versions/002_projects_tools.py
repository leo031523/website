"""add projects and tools

Revision ID: 002
Revises: 001
Create Date: 2026-06-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tools",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("url", sa.String(500)),
        sa.Column("icon_url", sa.String(500)),
        sa.Column("description", sa.Text),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), unique=True, nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("content_md", sa.Text, nullable=False, server_default=""),
        sa.Column("tech_stack", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("repo_url", sa.String(500)),
        sa.Column("demo_url", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.CheckConstraint("status IN ('draft', 'published')", name="ck_projects_status"),
        sa.Column("featured", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "cover_image_id",
            sa.Integer,
            sa.ForeignKey("media.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "project_tags",
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer,
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "project_tools",
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tool_id",
            sa.Integer,
            sa.ForeignKey("tools.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("project_tools")
    op.drop_table("project_tags")
    op.drop_table("projects")
    op.drop_table("tools")
