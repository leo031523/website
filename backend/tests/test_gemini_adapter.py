import httpx
import pytest
import respx
from app.services.ai.base import (
    ERROR_AUTH_FAILED,
    ERROR_MALFORMED_RESPONSE,
    ERROR_RATE_LIMITED,
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ChatMessage,
    ProviderError,
)
from app.services.ai.gemini import GeminiAdapter

_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def _success_body(text: str = "ok"):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


@pytest.mark.asyncio
@respx.mock
async def test_chat_success_returns_text():
    respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body("hello there")))

    adapter = GeminiAdapter()
    result = await adapter.chat(
        api_key="fake-key",
        model="gemini-2.0-flash",
        system_prompt="be nice",
        messages=[ChatMessage(role="user", content="hi")],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    assert result.text == "hello there"
    assert result.latency_ms >= 0


@pytest.mark.asyncio
@respx.mock
async def test_chat_maps_assistant_role_to_model():
    route = respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body()))

    adapter = GeminiAdapter()
    await adapter.chat(
        api_key="fake-key",
        model="gemini-2.0-flash",
        system_prompt="sys",
        messages=[
            ChatMessage(role="user", content="q1"),
            ChatMessage(role="assistant", content="a1"),
        ],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    sent = route.calls[0].request
    import json

    body = json.loads(sent.content)
    roles = [c["role"] for c in body["contents"]]
    assert roles == ["user", "model"]


@pytest.mark.asyncio
@respx.mock
async def test_chat_401_raises_auth_failed_without_retry():
    route = respx.post(_URL).mock(return_value=httpx.Response(401, json={"error": "nope"}))

    adapter = GeminiAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="bad-key",
            model="gemini-2.0-flash",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_AUTH_FAILED
    assert route.call_count == 1  # 認證失敗不重試


@pytest.mark.asyncio
@respx.mock
async def test_chat_invalid_api_key_400_maps_to_auth_failed():
    """Gemini 對無效 API key 實測回傳的是 400（不是常見的 401/403），
    body 裡帶 reason: API_KEY_INVALID，必須正確歸類成認證失敗、且不重試。
    這是對照真實 Gemini API 回應格式寫的迴歸測試。"""
    body = {
        "error": {
            "code": 400,
            "message": "API key not valid. Please pass a valid API key.",
            "status": "INVALID_ARGUMENT",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "API_KEY_INVALID",
                    "domain": "googleapis.com",
                }
            ],
        }
    }
    route = respx.post(_URL).mock(return_value=httpx.Response(400, json=body))

    adapter = GeminiAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="bad-key",
            model="gemini-2.0-flash",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_AUTH_FAILED
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_chat_429_retries_then_raises_rate_limited():
    route = respx.post(_URL).mock(return_value=httpx.Response(429, json={"error": "slow down"}))

    adapter = GeminiAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gemini-2.0-flash",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_RATE_LIMITED
    assert route.call_count == 3  # 初次 + 2 次重試


@pytest.mark.asyncio
@respx.mock
async def test_chat_500_retries_then_raises_unavailable():
    route = respx.post(_URL).mock(return_value=httpx.Response(500))

    adapter = GeminiAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gemini-2.0-flash",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_UNAVAILABLE
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_chat_timeout_raises_timeout_category():
    respx.post(_URL).mock(side_effect=httpx.TimeoutException("boom"))

    adapter = GeminiAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gemini-2.0-flash",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_TIMEOUT


@pytest.mark.asyncio
@respx.mock
async def test_chat_malformed_response_raises_malformed_category():
    respx.post(_URL).mock(return_value=httpx.Response(200, json={"unexpected": "shape"}))

    adapter = GeminiAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gemini-2.0-flash",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_MALFORMED_RESPONSE


@pytest.mark.asyncio
@respx.mock
async def test_chat_sends_api_key_via_header_not_url():
    """API key 一定要放在 header，不能放在 URL query string ——
    放在 URL 的話很容易被代理伺服器、httpx 自己的預設 log 等第三方
    工具意外記錄下來。"""
    route = respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body()))

    adapter = GeminiAdapter()
    await adapter.chat(
        api_key="super-secret-key-999",
        model="gemini-2.0-flash",
        system_prompt="sys",
        messages=[ChatMessage(role="user", content="hi")],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    sent = route.calls[0].request
    assert b"super-secret-key-999" not in sent.content
    assert "super-secret-key-999" not in str(sent.url)
    assert sent.headers["x-goog-api-key"] == "super-secret-key-999"
