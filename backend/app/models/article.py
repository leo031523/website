from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .tag import Tag, article_tags


class ArticleStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ArticleStatus] = mapped_column(
        String(20),
        nullable=False,
        server_default="draft",
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    cover_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    author: Mapped[User] = relationship()  # noqa: F821
    category: Mapped[Category | None] = relationship(back_populates="articles")  # noqa: F821
    cover_image: Mapped[Media | None] = relationship()  # noqa: F821
    tags: Mapped[list[Tag]] = relationship(secondary=article_tags, lazy="selectin")

    @property
    def cover_image_url(self) -> str | None:
        return f"/uploads/{self.cover_image.filename}" if self.cover_image else None
