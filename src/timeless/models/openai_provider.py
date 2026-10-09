import os
from typing import Any

from openai import APIError, OpenAI

from timeless.config import resolve_api_key
from timeless.models.provider import ModelProvider
from timeless.models.schemas import (
    MissingAPIKeyError,
    ModelResponse,
    ProviderAPIError,
    TokenUsage,
)


class OpenAIProvider(ModelProvider):
    """OpenAI model provider implementation."""

    DEFAULT_MODEL = "gpt-4o"
    ENV_VAR = "OPENAI_API_KEY"

    def __init__(self, api_key: str | None = None, client: Any | None = None) -> None:
        key = resolve_api_key("openai", api_key) or os.environ.get(self.ENV_VAR)
        if not key:
            raise MissingAPIKeyError("OpenAI", self.ENV_VAR)
        self.client = client or OpenAI(api_key=key)

    def generate(self, prompt: str, model: str | None = None) -> ModelResponse:
        target_model = model or self.DEFAULT_MODEL
        try:
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": prompt}],
            )
        except APIError as e:
            raise ProviderAPIError("OpenAI", str(e)) from e
        except Exception as e:
            raise ProviderAPIError("OpenAI", "An unexpected error occurred.") from e

        text = ""
        if response.choices and response.choices[0].message:
            text = response.choices[0].message.content or ""

        usage = TokenUsage()
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return ModelResponse(text=text, usage=usage, raw_response=response)
