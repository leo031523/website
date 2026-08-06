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
from app.services.ai.claude import ClaudeAdapter

_URL = "https://api.anthropic.com/v1/messages"


def _success_body(text: str = "ok"):
    return {"content": [{"type": "text", "text": text}]}


@pytest.mark.asyncio
@respx.mock
async def test_chat_success_returns_text():
    respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body("hello there")))

    adapter = ClaudeAdapter()
    result = await adapter.chat(
        api_key="fake-key",
        model="claude-3-5-haiku-20241022",
        system_prompt="be nice",
        messages=[ChatMessage(role="user", content="hi")],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    assert result.text == "hello there"
    assert result.latency_ms >= 0


@pytest.mark.asyncio
@respx.mock
async def test_chat_puts_system_prompt_in_top_level_field_not_messages():
    """Claude 的 system prompt 是獨立的頂層欄位，不是 messages 裡的一則
    訊息——這裡確認 payload 組得對，且 messages 只包含 user/assistant。"""
    route = respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body()))

    adapter = ClaudeAdapter()
    await adapter.chat(
        api_key="fake-key",
        model="claude-3-5-haiku-20241022",
        system_prompt="這是系統提示詞",
        messages=[
            ChatMessage(role="user", content="q1"),
            ChatMessage(role="assistant", content="a1"),
        ],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    import json

    body = json.loads(route.calls[0].request.content)
    assert body["system"] == "這是系統提示詞"
    assert [m["role"] for m in body["messages"]] == ["user", "assistant"]


@pytest.mark.asyncio
@respx.mock
async def test_chat_401_raises_auth_failed_without_retry():
    route = respx.post(_URL).mock(
        return_value=httpx.Response(
            401, json={"error": {"type": "authentication_error", "message": "invalid x-api-key"}}
        )
    )

    adapter = ClaudeAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="bad-key",
            model="claude-3-5-haiku-20241022",
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
    route = respx.post(_URL).mock(
        return_value=httpx.Response(429, json={"error": {"type": "rate_limit_error"}})
    )

    adapter = ClaudeAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="claude-3-5-haiku-20241022",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_RATE_LIMITED
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_chat_529_overloaded_retries_then_raises_unavailable():
    """529 是 Anthropic 專屬的「服務暫時過載」狀態碼，不是常見的 5xx
    範圍語意（其他 provider 通常用標準 5xx），要特別處理。"""
    route = respx.post(_URL).mock(
        return_value=httpx.Response(529, json={"error": {"type": "overloaded_error"}})
    )

    adapter = ClaudeAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="claude-3-5-haiku-20241022",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_UNAVAILABLE
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_chat_500_retries_then_raises_unavailable():
    route = respx.post(_URL).mock(return_value=httpx.Response(500))

    adapter = ClaudeAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="claude-3-5-haiku-20241022",
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

    adapter = ClaudeAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="claude-3-5-haiku-20241022",
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

    adapter = ClaudeAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="claude-3-5-haiku-20241022",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_MALFORMED_RESPONSE


@pytest.mark.asyncio
@respx.mock
async def test_chat_sends_api_key_via_header_not_url():
    route = respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body()))

    adapter = ClaudeAdapter()
    await adapter.chat(
        api_key="super-secret-key-999",
        model="claude-3-5-haiku-20241022",
        system_prompt="sys",
        messages=[ChatMessage(role="user", content="hi")],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    sent = route.calls[0].request
    assert b"super-secret-key-999" not in sent.content
    assert "super-secret-key-999" not in str(sent.url)
    assert sent.headers["x-api-key"] == "super-secret-key-999"
