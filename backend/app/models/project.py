from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

from .base import Base
from .tag import Tag
from .tool import Tool

# Junction tables
project_tags = Table(
    "project_tags",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

project_tools = Table(
    "project_tools",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("tool_id", ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    tech_stack: Mapped[list] = mapped_column(JSON, nullable=False, server_default="[]")
    repo_url: Mapped[str | None] = mapped_column(String(500))
    demo_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    cover_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    cover_image: Mapped[Media | None] = relationship()  # noqa: F821
    tags: Mapped[list[Tag]] = relationship(secondary=project_tags, lazy="selectin")
    tools: Mapped[list[Tool]] = relationship(secondary=project_tools, lazy="selectin")

    @property
    def cover_image_url(self) -> str | None:
        return f"/uploads/{self.cover_image.filename}" if self.cover_image else None
