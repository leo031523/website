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
from app.services.ai.openai import OpenAIAdapter

_URL = "https://api.openai.com/v1/chat/completions"


def _success_body(text: str = "ok"):
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


@pytest.mark.asyncio
@respx.mock
async def test_chat_success_returns_text():
    respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body("hello there")))

    adapter = OpenAIAdapter()
    result = await adapter.chat(
        api_key="fake-key",
        model="gpt-4o-mini",
        system_prompt="be nice",
        messages=[ChatMessage(role="user", content="hi")],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    assert result.text == "hello there"
    assert result.latency_ms >= 0


@pytest.mark.asyncio
@respx.mock
async def test_chat_sends_system_prompt_and_history_in_order():
    route = respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body()))

    adapter = OpenAIAdapter()
    await adapter.chat(
        api_key="fake-key",
        model="gpt-4o-mini",
        system_prompt="sys",
        messages=[
            ChatMessage(role="user", content="q1"),
            ChatMessage(role="assistant", content="a1"),
        ],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    import json

    body = json.loads(route.calls[0].request.content)
    assert body["messages"][0] == {"role": "system", "content": "sys"}
    assert [m["role"] for m in body["messages"][1:]] == ["user", "assistant"]


@pytest.mark.asyncio
@respx.mock
async def test_chat_401_raises_auth_failed_without_retry():
    route = respx.post(_URL).mock(
        return_value=httpx.Response(401, json={"error": {"message": "invalid api key"}})
    )

    adapter = OpenAIAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="bad-key",
            model="gpt-4o-mini",
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
        return_value=httpx.Response(429, json={"error": {"message": "slow down"}})
    )

    adapter = OpenAIAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gpt-4o-mini",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_RATE_LIMITED
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_chat_500_retries_then_raises_unavailable():
    route = respx.post(_URL).mock(return_value=httpx.Response(500))

    adapter = OpenAIAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gpt-4o-mini",
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

    adapter = OpenAIAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gpt-4o-mini",
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

    adapter = OpenAIAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="gpt-4o-mini",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
        )
    assert exc_info.value.category == ERROR_MALFORMED_RESPONSE


@pytest.mark.asyncio
@respx.mock
async def test_chat_sends_api_key_via_bearer_header_not_url():
    route = respx.post(_URL).mock(return_value=httpx.Response(200, json=_success_body()))

    adapter = OpenAIAdapter()
    await adapter.chat(
        api_key="super-secret-key-999",
        model="gpt-4o-mini",
        system_prompt="sys",
        messages=[ChatMessage(role="user", content="hi")],
        timeout_seconds=5,
        max_output_tokens=16,
    )
    sent = route.calls[0].request
    assert b"super-secret-key-999" not in sent.content
    assert "super-secret-key-999" not in str(sent.url)
    assert sent.headers["authorization"] == "Bearer super-secret-key-999"
