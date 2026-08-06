from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AboutContent(Base):
    """單一列（id=1）的「關於我」內容，取代原本寫死在前端頁面的文字，
    讓後台可以編輯，AI 助理之後也才有辦法檢索這份內容。"""

    __tablename__ = "about_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
