from unittest.mock import MagicMock

import pytest
from google.genai.errors import APIError as GeminiAPIError
from openai import APIError as OpenAIAPIError

from timeless.models import (
    AnthropicProvider,
    GeminiProvider,
    MissingAPIKeyError,
    OpenAIProvider,
    ProviderAPIError,
    get_provider,
)


def test_openai_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError) as exc_info:
        OpenAIProvider()
    assert "OPENAI_API_KEY" in str(exc_info.value)


def test_openai_generate_success() -> None:
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "OpenAI response text"
    mock_usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_response = MagicMock(choices=[mock_choice], usage=mock_usage)
    mock_client.chat.completions.create.return_value = mock_response

    provider = OpenAIProvider(api_key="test-key", client=mock_client)
    response = provider.generate("Hello OpenAI")

    assert response.text == "OpenAI response text"
    assert response.usage.prompt_tokens == 10
    assert response.usage.completion_tokens == 20
    assert response.usage.total_tokens == 30
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello OpenAI"}],
    )


def test_openai_generate_error() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = OpenAIAPIError(
        message="Quota exceeded", body=None, request=MagicMock()
    )

    provider = OpenAIProvider(api_key="test-key", client=mock_client)
    with pytest.raises(ProviderAPIError) as exc_info:
        provider.generate("Hello OpenAI")
    assert "Quota exceeded" in str(exc_info.value)


def test_anthropic_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError) as exc_info:
        AnthropicProvider()
    assert "ANTHROPIC_API_KEY" in str(exc_info.value)


def test_anthropic_generate_success() -> None:
    mock_client = MagicMock()
    mock_block = MagicMock(text="Claude response text")
    mock_usage = MagicMock(input_tokens=15, output_tokens=25)
    mock_response = MagicMock(content=[mock_block], usage=mock_usage)
    mock_client.messages.create.return_value = mock_response

    provider = AnthropicProvider(api_key="test-key", client=mock_client)
    response = provider.generate("Hello Claude")

    assert response.text == "Claude response text"
    assert response.usage.prompt_tokens == 15
    assert response.usage.completion_tokens == 25
    assert response.usage.total_tokens == 40
    mock_client.messages.create.assert_called_once_with(
        model="claude-3-5-sonnet-latest",
        max_tokens=4096,
        messages=[{"role": "user", "content": "Hello Claude"}],
    )


def test_gemini_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError) as exc_info:
        GeminiProvider()
    assert "GEMINI_API_KEY" in str(exc_info.value)


def test_gemini_fallback_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "fallback-key")
    mock_client = MagicMock()
    provider = GeminiProvider(client=mock_client)
    assert provider is not None


def test_gemini_generate_success() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Gemini response text"
    mock_response.usage_metadata.prompt_token_count = 5
    mock_response.usage_metadata.candidates_token_count = 15
    mock_response.usage_metadata.total_token_count = 20
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider(api_key="test-key", client=mock_client)
    response = provider.generate("Hello Gemini")

    assert response.text == "Gemini response text"
    assert response.usage.prompt_tokens == 5
    assert response.usage.completion_tokens == 15
    assert response.usage.total_tokens == 20
    mock_client.models.generate_content.assert_called_once_with(
        model="gemini-2.5-flash",
        contents="Hello Gemini",
    )


def test_gemini_generate_error() -> None:
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = GeminiAPIError(
        400, {"message": "Invalid argument"}
    )

    provider = GeminiProvider(api_key="test-key", client=mock_client)
    with pytest.raises(ProviderAPIError) as exc_info:
        provider.generate("Hello Gemini")
    assert "Invalid argument" in str(exc_info.value)


def test_get_provider_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "key1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key2")
    monkeypatch.setenv("GEMINI_API_KEY", "key3")

    p1 = get_provider("openai")
    assert isinstance(p1, OpenAIProvider)

    p2 = get_provider("claude")
    assert isinstance(p2, AnthropicProvider)

    p3 = get_provider("gemini")
    assert isinstance(p3, GeminiProvider)

    with pytest.raises(ValueError):
        get_provider("unknown")
