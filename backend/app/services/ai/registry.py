from app.models.ai_settings import AIProvider

from .base import ProviderAdapter
from .gemini import GeminiAdapter

_ADAPTERS: dict[AIProvider, ProviderAdapter] = {
    AIProvider.gemini: GeminiAdapter(),
}

# 目前只有 Gemini 有實際的 adapter 實作；其餘 provider 允許在設定頁建立、
# 但不可被啟用，避免啟用後第一次真正呼叫才發現整個 adapter 不存在。
SUPPORTED_PROVIDERS: frozenset[AIProvider] = frozenset(_ADAPTERS.keys())


def get_adapter(provider: AIProvider) -> ProviderAdapter:
    adapter = _ADAPTERS.get(provider)
    if adapter is None:
        raise NotImplementedError(f"provider {provider} 尚未實作 adapter")
    return adapter
