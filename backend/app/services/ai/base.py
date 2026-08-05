from abc import ABC, abstractmethod
from dataclasses import dataclass

# 安全化後的錯誤分類，供公開 API 回傳與 log 使用，絕不包含原始
# provider response、header 或 API key。
ERROR_NOT_CONFIGURED = "not_configured"
ERROR_AUTH_FAILED = "auth_failed"
ERROR_TIMEOUT = "timeout"
ERROR_UNAVAILABLE = "unavailable"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_BAD_REQUEST = "bad_request"
ERROR_MALFORMED_RESPONSE = "malformed_response"
ERROR_RESPONSE_TOO_LARGE = "response_too_large"
ERROR_UNKNOWN = "unknown"


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class ChatResult:
    text: str
    latency_ms: float


class ProviderError(Exception):
    """統一的 provider 呼叫錯誤。message 只給後端 log 使用，公開 API
    只能回傳 category，避免洩漏 provider 原始錯誤內容。"""

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


class ProviderAdapter(ABC):
    @abstractmethod
    async def chat(
        self,
        *,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: list[ChatMessage],
        timeout_seconds: float,
        max_output_tokens: int,
        base_url: str | None = None,
    ) -> ChatResult:
        """呼叫底層模型，回傳文字結果。失敗時拋出 ProviderError。"""
        raise NotImplementedError
