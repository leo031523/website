from . import _openai_style
from .base import ChatMessage, ChatResult, ProviderAdapter

# 官方 endpoint 寫死在程式內，不接受呼叫端傳入的 base_url，避免 SSRF。
_OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIAdapter(ProviderAdapter):
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
        return await _openai_style.chat_completions(
            base_url=_OPENAI_BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            model=model,
            system_prompt=system_prompt,
            messages=messages,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
