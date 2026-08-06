import httpx
import pytest
import respx
from app.core.config import settings
from app.services.ai.base import ERROR_AUTH_FAILED, ERROR_BAD_REQUEST, ChatMessage, ProviderError
from app.services.ai.openai_compatible import OpenAICompatibleAdapter


def _success_body(text: str = "ok"):
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


@pytest.mark.asyncio
async def test_chat_requires_base_url():
    adapter = OpenAICompatibleAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="llama3",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
            base_url=None,
        )
    assert exc_info.value.category == ERROR_BAD_REQUEST


@pytest.mark.asyncio
@respx.mock
async def test_chat_calls_custom_base_url():
    url = "http://localhost:11434/v1/chat/completions"
    route = respx.post(url).mock(return_value=httpx.Response(200, json=_success_body("hi from local model")))

    adapter = OpenAICompatibleAdapter()
    result = await adapter.chat(
        api_key="fake-key",
        model="llama3",
        system_prompt="sys",
        messages=[ChatMessage(role="user", content="hi")],
        timeout_seconds=5,
        max_output_tokens=16,
        base_url="http://localhost:11434/v1",
    )
    assert result.text == "hi from local model"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_chat_401_raises_auth_failed():
    url = "http://localhost:11434/v1/chat/completions"
    respx.post(url).mock(return_value=httpx.Response(401, json={"error": {"message": "nope"}}))

    adapter = OpenAICompatibleAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="bad-key",
            model="llama3",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
            base_url="http://localhost:11434/v1",
        )
    assert exc_info.value.category == ERROR_AUTH_FAILED


@pytest.mark.asyncio
async def test_chat_rejects_non_http_scheme_regardless_of_environment():
    adapter = OpenAICompatibleAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="llama3",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
            base_url="file:///etc/passwd",
        )
    assert exc_info.value.category == ERROR_BAD_REQUEST


@pytest.mark.asyncio
async def test_chat_allows_loopback_in_development_by_default(monkeypatch):
    """本機開發預設可以直接連到 loopback（例如本機跑的 Ollama），不需要
    額外設定——SSRF 檢查只在正式環境套用。"""
    monkeypatch.setattr(settings, "app_env", "development")
    with respx.mock:
        url = "http://127.0.0.1:11434/v1/chat/completions"
        respx.post(url).mock(return_value=httpx.Response(200, json=_success_body()))

        adapter = OpenAICompatibleAdapter()
        result = await adapter.chat(
            api_key="fake-key",
            model="llama3",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
            base_url="http://127.0.0.1:11434/v1",
        )
        assert result.text == "ok"


@pytest.mark.asyncio
async def test_chat_rejects_loopback_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    adapter = OpenAICompatibleAdapter()
    with pytest.raises(ProviderError) as exc_info:
        await adapter.chat(
            api_key="fake-key",
            model="llama3",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
            base_url="http://127.0.0.1:11434/v1",
        )
    assert exc_info.value.category == ERROR_BAD_REQUEST


@pytest.mark.asyncio
async def test_chat_rejects_cloud_metadata_ip_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    adapter = OpenAICompatibleAdapter()
    with pytest.raises(ProviderError):
        await adapter.chat(
            api_key="fake-key",
            model="llama3",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
            base_url="http://169.254.169.254/latest/meta-data",
        )


@pytest.mark.asyncio
async def test_chat_allows_allowlisted_host_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "ai_local_model_allowlist", "localhost")
    with respx.mock:
        url = "http://localhost:11434/v1/chat/completions"
        respx.post(url).mock(return_value=httpx.Response(200, json=_success_body()))

        adapter = OpenAICompatibleAdapter()
        result = await adapter.chat(
            api_key="fake-key",
            model="llama3",
            system_prompt="sys",
            messages=[ChatMessage(role="user", content="hi")],
            timeout_seconds=5,
            max_output_tokens=16,
            base_url="http://localhost:11434/v1",
        )
        assert result.text == "ok"
