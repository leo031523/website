import asyncio

from . import _openai_style
from .base import ERROR_BAD_REQUEST, ChatMessage, ChatResult, ProviderAdapter, ProviderError
from .url_validation import UnsafeProviderURLError, validate_provider_base_url


class OpenAICompatibleAdapter(ProviderAdapter):
    """給自架或第三方相容服務用（例如本機的 Ollama、LM Studio，或任何
    實作 OpenAI /chat/completions 介面的服務）。這是唯一允許使用者自訂
    base_url 的 provider，所以呼叫前一定要先做 SSRF 檢查——測試連線
    與正式聊天走同一個 chat()，兩邊自動套用同一套 URL 驗證。"""

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
        if not base_url:
            raise ProviderError(ERROR_BAD_REQUEST, "OpenAI-compatible provider 缺少 base_url")

        try:
            # DNS 解析是同步／阻塞的系統呼叫，丟到 thread 裡跑，不要卡住
            # 事件迴圈。
            await asyncio.to_thread(validate_provider_base_url, base_url)
        except UnsafeProviderURLError as exc:
            raise ProviderError(ERROR_BAD_REQUEST, str(exc)) from exc

        return await _openai_style.chat_completions(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            model=model,
            system_prompt=system_prompt,
            messages=messages,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
