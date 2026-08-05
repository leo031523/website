from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.ai_settings import AIProvider


class AIProviderSettingsCreate(BaseModel):
    provider: AIProvider
    model: str
    base_url: str | None = None
    api_key: str | None = None
    timeout_seconds: int = 30
    max_output_tokens: int = 1024
    top_k: int = 5

    @model_validator(mode="after")
    def _require_base_url_for_compatible(self) -> "AIProviderSettingsCreate":
        if self.provider == AIProvider.openai_compatible and not self.base_url:
            raise ValueError("openai_compatible provider 必須提供 base_url")
        if self.provider != AIProvider.openai_compatible and self.base_url:
            raise ValueError("只有 openai_compatible provider 可以自訂 base_url")
        return self


class AIProviderSettingsUpdate(BaseModel):
    model: str | None = None
    base_url: str | None = None
    # api_key 留空（None）＝保留原本的 key；要移除必須明確帶 remove_api_key=true，
    # 不會因為欄位留空就被誤刪。
    api_key: str | None = None
    remove_api_key: bool = False
    timeout_seconds: int | None = None
    max_output_tokens: int | None = None
    top_k: int | None = None


class AIProviderSettingsResponse(BaseModel):
    id: int
    provider: AIProvider
    model: str
    base_url: str | None
    is_configured: bool
    api_key_suffix: str | None
    is_enabled: bool
    timeout_seconds: int
    max_output_tokens: int
    top_k: int
    created_at: datetime
    updated_at: datetime
