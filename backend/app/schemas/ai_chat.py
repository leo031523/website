from typing import Literal

from pydantic import BaseModel, field_validator

_MAX_MESSAGE_LENGTH = 2000
_MAX_HISTORY_TURNS = 10
_MAX_HISTORY_TOTAL_CHARS = 8000


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryMessage] = []

    @field_validator("message")
    @classmethod
    def _validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("訊息不可為空")
        if len(v) > _MAX_MESSAGE_LENGTH:
            raise ValueError(f"訊息長度不可超過 {_MAX_MESSAGE_LENGTH} 字元")
        return v

    @field_validator("history")
    @classmethod
    def _validate_history(cls, v: list[ChatHistoryMessage]) -> list[ChatHistoryMessage]:
        if len(v) > _MAX_HISTORY_TURNS:
            raise ValueError(f"對話歷史最多 {_MAX_HISTORY_TURNS} 則")
        total_chars = sum(len(m.content) for m in v)
        if total_chars > _MAX_HISTORY_TOTAL_CHARS:
            raise ValueError("對話歷史內容過長")
        return v


class ChatSource(BaseModel):
    id: str
    title: str
    url: str
    source_type: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    provider: str
    model: str
    request_id: str
    # sources 非空時為 True；沒有檢索到相關內容、或模型的回答沒有任何
    # 有效引用時為 False（此時 answer 會是固定的「沒有足夠資訊」文字，
    # 而不是模型自己生成、卻沒有引用佐證的內容）。
    grounded: bool
