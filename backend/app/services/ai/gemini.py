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
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_MAX_RESPONSE_BYTES = 1_000_000  # Gemini 官方回應正常遠小於此，超過視為異常
_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = (0.5, 1.5)
_INVALID_KEY_REASONS = {"API_KEY_INVALID", "API_KEY_SERVICE_BLOCKED", "API_KEY_PERMISSION_DENIED"}


def _is_invalid_api_key_error(response: httpx.Response) -> bool:
    try:
        details = response.json().get("error", {}).get("details", [])
    except ValueError:
        return False
    return any(d.get("reason") in _INVALID_KEY_REASONS for d in details)


class GeminiAdapter(ProviderAdapter):
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
        url = f"{_GEMINI_BASE_URL}/models/{model}:generateContent"
        payload = {
            "contents": [
                {
                    "role": "model" if m.role == "assistant" else "user",
                    "parts": [{"text": m.content}],
                }
                for m in messages
            ],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"maxOutputTokens": max_output_tokens},
        }

        last_error: ProviderError | None = None
        start = time.monotonic()

        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                    # 用 header 而不是 ?key= query string 傳遞 API key，
                    # 避免金鑰出現在 URL 裡（URL 比 header 更容易被第三方
                    # 中介軟體、代理伺服器或 log 工具意外記錄下來）。
                    response = await client.post(
                        url, headers={"x-goog-api-key": api_key}, json=payload
                    )
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
                elif response.status_code >= 500:
                    last_error = ProviderError(ERROR_UNAVAILABLE, f"provider 回傳 {response.status_code}")
                elif response.status_code >= 400:
                    # Gemini 對無效 API key 實測回傳的是 400 + reason
                    # "API_KEY_INVALID"，不是常見的 401/403，須另外判斷。
                    if _is_invalid_api_key_error(response):
                        raise ProviderError(ERROR_AUTH_FAILED, "API key 認證失敗")
                    raise ProviderError(ERROR_BAD_REQUEST, f"請求格式錯誤：{response.status_code}")
                else:
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > _MAX_RESPONSE_BYTES:
                        raise ProviderError(ERROR_RESPONSE_TOO_LARGE, "provider 回應過大")
                    if len(response.content) > _MAX_RESPONSE_BYTES:
                        raise ProviderError(ERROR_RESPONSE_TOO_LARGE, "provider 回應過大")

                    try:
                        data = response.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError, ValueError) as exc:
                        raise ProviderError(ERROR_MALFORMED_RESPONSE, f"無法解析回應：{exc}") from exc

                    return ChatResult(text=text, latency_ms=latency_ms)

            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_BACKOFF_SECONDS[attempt])

        assert last_error is not None
        raise last_error
