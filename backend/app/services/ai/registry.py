from app.models.ai_settings import AIProvider

from .base import ProviderAdapter
from .gemini import GeminiAdapter

_ADAPTERS: dict[AIProvider, ProviderAdapter] = {
    AIProvider.gemini: GeminiAdapter(),
}


def get_adapter(provider: AIProvider) -> ProviderAdapter:
    adapter = _ADAPTERS.get(provider)
    if adapter is None:
        raise NotImplementedError(f"provider {provider} 尚未實作 adapter")
    return adapter
