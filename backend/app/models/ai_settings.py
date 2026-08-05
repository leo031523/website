from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AIProvider(str, enum.Enum):
    gemini = "gemini"
    openai = "openai"
    claude = "claude"
    openai_compatible = "openai_compatible"


class AIProviderSettings(Base):
    """一份 AI provider 設定。同一時間最多只有一筆 is_enabled=True
    （DB 有 partial unique index 保證，切換 provider 時也在同一筆
    transaction 內先停用舊的再啟用新的）。"""

    __tablename__ = "ai_provider_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[AIProvider] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    # 只有 openai_compatible 可以自訂 base_url；其餘 provider 使用程式內建的官方 endpoint
    base_url: Mapped[str | None] = mapped_column(String(500))
    # Fernet 加密後的密文，不存明文
    encrypted_api_key: Mapped[str | None] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    max_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1024")
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
