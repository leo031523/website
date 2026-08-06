"""add about_content

Revision ID: 005
Revises: 004
Create Date: 2026-08-05

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 種子內容延用原本寫死在 frontend/app/about/page.tsx 的文字，
# 讓這次遷移不會改變網站現有畫面。
_SEED_CONTENT_MD = (
    "這是一個個人筆記與作品集網站，記錄學習過的技術、使用過的工具，以及開發過的專案。\n"
    "\n"
    "網站本身就是一件作品——前後端分離、SSG/ISR、後台 CMS、Docker 部署，"
    "每一個環節都是可評估的工程展示。"
)


def upgrade() -> None:
    op.create_table(
        "about_content",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("content_md", sa.Text, nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    about_content = sa.table(
        "about_content",
        sa.column("id", sa.Integer),
        sa.column("content_md", sa.Text),
    )
    op.bulk_insert(about_content, [{"id": 1, "content_md": _SEED_CONTENT_MD}])


def downgrade() -> None:
    op.drop_table("about_content")
