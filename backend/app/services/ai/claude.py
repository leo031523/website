import asyncio
import time

import httpx

from .base import (
    ERROR_AUTH_FAILED,
    ERROR_BAD_REQUEST,
    ERROR_MALFORMED_RESPONSE,
    ERROR_RATE_LIMITED,
    ERROR_RESPONSE_TOO_LARGE,
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ChatMessage,
    ChatResult,
    ProviderAdapter,
    ProviderError,
)

# 官方 endpoint 寫死在程式內，不接受呼叫端傳入的 base_url，避免 SSRF。
_CLAUDE_BASE_URL = "https://api.anthropic.com/v1"
_ANTHROPIC_VERSION = "2023-06-01"
_MAX_RESPONSE_BYTES = 1_000_000
_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = (0.5, 1.5)


class ClaudeAdapter(ProviderAdapter):
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
        url = f"{_CLAUDE_BASE_URL}/messages"
        # Claude 的 system prompt 是獨立的頂層欄位，不是 messages 陣列裡
        # 的一則訊息；messages 只接受 user/assistant，剛好對應我們自己
        # 的 ChatMessage.role，不需要像 Gemini 那樣做角色名稱轉換。
        payload = {
            "model": model,
            "system": system_prompt,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_output_tokens,
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        }

        last_error: ProviderError | None = None
        start = time.monotonic()

        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                last_error = ProviderError(ERROR_TIMEOUT, f"逾時：{exc}")
            except httpx.RequestError as exc:
                last_error = ProviderError(ERROR_UNAVAILABLE, f"連線失敗：{exc}")
            else:
                latency_ms = (time.monotonic() - start) * 1000

                if response.status_code in (401, 403):
                    raise ProviderError(ERROR_AUTH_FAILED, "API key 認證失敗")
                if response.status_code == 429:
                    last_error = ProviderError(ERROR_RATE_LIMITED, "已達 provider 的請求頻率限制")
                elif response.status_code == 529:
                    # Anthropic 專屬的「服務暫時過載」狀態碼
                    last_error = ProviderError(ERROR_UNAVAILABLE, "provider 暫時過載")
                elif response.status_code >= 500:
                    last_error = ProviderError(ERROR_UNAVAILABLE, f"provider 回傳 {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(ERROR_BAD_REQUEST, f"請求格式錯誤：{response.status_code}")
                else:
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > _MAX_RESPONSE_BYTES:
                        raise ProviderError(ERROR_RESPONSE_TOO_LARGE, "provider 回應過大")
                    if len(response.content) > _MAX_RESPONSE_BYTES:
                        raise ProviderError(ERROR_RESPONSE_TOO_LARGE, "provider 回應過大")

                    try:
                        data = response.json()
                        text = data["content"][0]["text"]
                    except (KeyError, IndexError, ValueError) as exc:
                        raise ProviderError(ERROR_MALFORMED_RESPONSE, f"無法解析回應：{exc}") from exc

                    return ChatResult(text=text, latency_ms=latency_ms)

            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_BACKOFF_SECONDS[attempt])

        assert last_error is not None
        raise last_error
