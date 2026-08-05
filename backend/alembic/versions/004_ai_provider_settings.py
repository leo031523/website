"""add ai_provider_settings

Revision ID: 004
Revises: 003
Create Date: 2026-08-05

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_provider_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("base_url", sa.String(500)),
        sa.Column("encrypted_api_key", sa.Text),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("timeout_seconds", sa.Integer, nullable=False, server_default="30"),
        sa.Column("max_output_tokens", sa.Integer, nullable=False, server_default="1024"),
        sa.Column("top_k", sa.Integer, nullable=False, server_default="5"),
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
    # 同一時間最多只能有一筆 is_enabled = true
    op.create_index(
        "ix_ai_provider_settings_one_enabled",
        "ai_provider_settings",
        ["is_enabled"],
        unique=True,
        postgresql_where=sa.text("is_enabled = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_ai_provider_settings_one_enabled", table_name="ai_provider_settings")
    op.drop_table("ai_provider_settings")
