import os
from typing import Any

from google import genai
from google.genai.errors import APIError

from timeless.config import resolve_api_key
from timeless.models.provider import ModelProvider
from timeless.models.schemas import (
    MissingAPIKeyError,
    ModelResponse,
    ProviderAPIError,
    TokenUsage,
)


class GeminiProvider(ModelProvider):
    """Google Gemini model provider implementation using google-genai SDK."""

    DEFAULT_MODEL = "gemini-2.5-flash"
    PRIMARY_ENV_VAR = "GEMINI_API_KEY"
    FALLBACK_ENV_VAR = "GOOGLE_API_KEY"

    def __init__(self, api_key: str | None = None, client: Any | None = None) -> None:
        key = (
            resolve_api_key("gemini", api_key)
            or os.environ.get(self.PRIMARY_ENV_VAR)
            or os.environ.get(self.FALLBACK_ENV_VAR)
        )
        if not key:
            raise MissingAPIKeyError("Gemini", self.PRIMARY_ENV_VAR)
        self.client = client or genai.Client(api_key=key)

    def generate(self, prompt: str, model: str | None = None) -> ModelResponse:
        target_model = model or self.DEFAULT_MODEL
        try:
            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt,
            )
        except APIError as e:
            raise ProviderAPIError("Gemini", str(e)) from e
        except Exception as e:
            raise ProviderAPIError("Gemini", "An unexpected error occurred.") from e

        text = getattr(response, "text", "") or ""

        usage = TokenUsage()
        metadata = getattr(response, "usage_metadata", None)
        if metadata:
            prompt_tokens = getattr(metadata, "prompt_token_count", None)
            completion_tokens = getattr(metadata, "candidates_token_count", None)
            total_tokens = getattr(metadata, "total_token_count", None)
            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

        return ModelResponse(text=text, usage=usage, raw_response=response)
