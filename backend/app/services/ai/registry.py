from app.models.ai_settings import AIProvider

from .base import ProviderAdapter
from .claude import ClaudeAdapter
from .gemini import GeminiAdapter
from .openai import OpenAIAdapter
from .openai_compatible import OpenAICompatibleAdapter

_ADAPTERS: dict[AIProvider, ProviderAdapter] = {
    AIProvider.gemini: GeminiAdapter(),
    AIProvider.openai: OpenAIAdapter(),
    AIProvider.claude: ClaudeAdapter(),
    AIProvider.openai_compatible: OpenAICompatibleAdapter(),
}

# get_adapter() 找不到 adapter 時會丟 NotImplementedError；/enable、/test
# 兩個路由用這個集合提前擋下沒有 adapter 的 provider，不用等到真正呼叫
# 才發現整個 adapter 不存在。目前四種 provider 都已經實作。
SUPPORTED_PROVIDERS: frozenset[AIProvider] = frozenset(_ADAPTERS.keys())


def get_adapter(provider: AIProvider) -> ProviderAdapter:
    adapter = _ADAPTERS.get(provider)
    if adapter is None:
        raise NotImplementedError(f"provider {provider} 尚未實作 adapter")
    return adapter
