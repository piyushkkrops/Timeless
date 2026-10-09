from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ModelResponse:
    text: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    raw_response: Any = None


class ModelProviderError(Exception):
    """Base exception for model provider errors."""

    pass


class MissingAPIKeyError(ModelProviderError):
    """Raised when a required API key environment variable is missing."""

    def __init__(self, provider_name: str, env_var: str) -> None:
        self.provider_name = provider_name
        self.env_var = env_var
        super().__init__(
            f"Missing API key for {provider_name}. "
            f"Please set the {env_var} environment variable."
        )


class ProviderAPIError(ModelProviderError):
    """Raised when a model provider API call fails."""

    def __init__(self, provider_name: str, message: str) -> None:
        self.provider_name = provider_name
        super().__init__(f"{provider_name} API error: {message}")
