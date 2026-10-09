from timeless.models.anthropic_provider import AnthropicProvider
from timeless.models.gemini_provider import GeminiProvider
from timeless.models.openai_provider import OpenAIProvider
from timeless.models.provider import ModelProvider
from timeless.models.schemas import (
    MissingAPIKeyError,
    ModelProviderError,
    ModelResponse,
    ProviderAPIError,
    TokenUsage,
)


def get_provider(provider_name: str, api_key: str | None = None) -> ModelProvider:
    """Factory function to instantiate a model provider by name."""
    normalized = provider_name.lower().strip()
    if normalized == "openai":
        return OpenAIProvider(api_key=api_key)
    elif normalized in ("anthropic", "claude"):
        return AnthropicProvider(api_key=api_key)
    elif normalized in ("gemini", "google"):
        return GeminiProvider(api_key=api_key)
    else:
        raise ValueError(
            f"Unsupported provider '{provider_name}'. "
            "Supported providers: openai, anthropic, gemini."
        )


__all__ = [
    "AnthropicProvider",
    "GeminiProvider",
    "MissingAPIKeyError",
    "ModelProvider",
    "ModelProviderError",
    "ModelResponse",
    "OpenAIProvider",
    "ProviderAPIError",
    "TokenUsage",
    "get_provider",
]
