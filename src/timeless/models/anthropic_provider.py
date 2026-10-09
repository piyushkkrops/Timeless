import os
from typing import Any

from anthropic import Anthropic, APIError

from timeless.config import resolve_api_key
from timeless.models.provider import ModelProvider
from timeless.models.schemas import (
    MissingAPIKeyError,
    ModelResponse,
    ProviderAPIError,
    TokenUsage,
)


class AnthropicProvider(ModelProvider):
    """Anthropic model provider implementation."""

    DEFAULT_MODEL = "claude-3-5-sonnet-latest"
    DEFAULT_MAX_TOKENS = 4096
    ENV_VAR = "ANTHROPIC_API_KEY"

    def __init__(self, api_key: str | None = None, client: Any | None = None) -> None:
        key = resolve_api_key("anthropic", api_key) or os.environ.get(self.ENV_VAR)
        if not key:
            raise MissingAPIKeyError("Anthropic", self.ENV_VAR)
        self.client = client or Anthropic(api_key=key)

    def generate(self, prompt: str, model: str | None = None) -> ModelResponse:
        target_model = model or self.DEFAULT_MODEL
        try:
            response = self.client.messages.create(
                model=target_model,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
        except APIError as e:
            raise ProviderAPIError("Anthropic", str(e)) from e
        except Exception as e:
            raise ProviderAPIError("Anthropic", "An unexpected error occurred.") from e

        text = ""
        if response.content:
            text_blocks = [
                block.text for block in response.content if hasattr(block, "text")
            ]
            text = "".join(text_blocks)

        usage = TokenUsage()
        if hasattr(response, "usage") and response.usage:
            input_tokens = getattr(response.usage, "input_tokens", None)
            output_tokens = getattr(response.usage, "output_tokens", None)
            total = None
            if input_tokens is not None and output_tokens is not None:
                total = input_tokens + output_tokens
            usage = TokenUsage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total,
            )

        return ModelResponse(text=text, usage=usage, raw_response=response)
