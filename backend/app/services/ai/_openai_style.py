"""OpenAI 的 /chat/completions request/response 邏輯，OpenAI 官方
adapter 與 OpenAI-compatible（自架／第三方相容服務）adapter 共用同一套
處理與重試邏輯，差別只在 base_url 跟認證 header。"""

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
    ProviderError,
)

_MAX_RESPONSE_BYTES = 1_000_000
_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = (0.5, 1.5)


async def chat_completions(
    *,
    base_url: str,
    headers: dict[str, str],
    model: str,
    system_prompt: str,
    messages: list[ChatMessage],
    timeout_seconds: float,
    max_output_tokens: int,
) -> ChatResult:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *[{"role": m.role, "content": m.content} for m in messages],
        ],
        "max_tokens": max_output_tokens,
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
                    text = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, ValueError) as exc:
                    raise ProviderError(ERROR_MALFORMED_RESPONSE, f"無法解析回應：{exc}") from exc

                return ChatResult(text=text, latency_ms=latency_ms)

        if attempt < _MAX_RETRIES:
            await asyncio.sleep(_RETRY_BACKOFF_SECONDS[attempt])

    assert last_error is not None
    raise last_error
