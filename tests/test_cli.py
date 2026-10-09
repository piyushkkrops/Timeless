from unittest.mock import MagicMock, patch

import pytest

from timeless.cli.main import build_parser, main
from timeless.models import (
    MissingAPIKeyError,
    ModelResponse,
    ProviderAPIError,
)


def test_parse_args_defaults() -> None:
    parser = build_parser()
    args = parser.parse_args(["Fix bug"])
    assert args.prompt == "Fix bug"
    assert args.provider is None
    assert args.no_context is False
    assert args.search is None


def test_parse_args_provider_selection() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["-p", "anthropic", "--no-context", "-s", "search_term", "Fix bug"]
    )
    assert args.prompt == "Fix bug"
    assert args.provider == "anthropic"
    assert args.no_context is True
    assert args.search == "search_term"

    args = parser.parse_args(["--provider", "gemini", "Fix bug"])
    assert args.provider == "gemini"


def test_cli_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "timeless" in captured.out


@patch("timeless.cli.main.get_provider")
def test_main_success_with_context(
    mock_get_provider: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_provider = MagicMock()
    mock_provider.generate.return_value = ModelResponse(text="Generated code fix")
    mock_get_provider.return_value = mock_provider

    exit_code = main(["-p", "anthropic", "Refactor provider.py"])

    assert exit_code == 0
    mock_get_provider.assert_called_once_with("anthropic")
    mock_provider.generate.assert_called_once()
    called_prompt = mock_provider.generate.call_args[0][0]
    assert "[PROJECT CONTEXT]" in called_prompt
    assert "[USER PROMPT]\nRefactor provider.py\n[/USER_PROMPT]" in called_prompt

    captured = capsys.readouterr()
    assert "Generated code fix" in captured.out


@patch("timeless.cli.main.get_provider")
def test_main_search_flag(
    mock_get_provider: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_provider = MagicMock()
    mock_provider.generate.return_value = ModelResponse(text="Search result response")
    mock_get_provider.return_value = mock_provider

    exit_code = main(["-s", "provider", "Explain model providers"])

    assert exit_code == 0
    called_prompt = mock_provider.generate.call_args[0][0]
    assert "[SEARCH RESULTS for 'provider']" in called_prompt
    assert "[USER PROMPT]\nExplain model providers\n[/USER_PROMPT]" in called_prompt


@patch("timeless.cli.main.get_provider")
def test_main_no_context_flag(
    mock_get_provider: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_provider = MagicMock()
    mock_provider.generate.return_value = ModelResponse(text="Raw prompt response")
    mock_get_provider.return_value = mock_provider

    exit_code = main(["--no-context", "Refactor provider.py"])

    assert exit_code == 0
    mock_provider.generate.assert_called_once_with("Refactor provider.py")
    captured = capsys.readouterr()
    assert "Raw prompt response" in captured.out


@patch("timeless.cli.main.save_config")
def test_main_setup_command(
    mock_save: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["setup", "-p", "anthropic", "--api-key", "sk-ant-test"])

    assert exit_code == 0
    mock_save.assert_called_once()
    captured = capsys.readouterr()
    assert "Configuration saved to" in captured.out
    assert "sk-ant-test" not in captured.out


@patch("timeless.cli.main.get_provider")
def test_main_missing_credentials(
    mock_get_provider: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_get_provider.side_effect = MissingAPIKeyError("OpenAI", "OPENAI_API_KEY")

    exit_code = main(["Fix bug"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Missing API key for OpenAI" in captured.err


@patch("timeless.cli.main.get_provider")
def test_main_api_failure(
    mock_get_provider: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = ProviderAPIError(
        "OpenAI", "Rate limit exceeded"
    )
    mock_get_provider.return_value = mock_provider

    exit_code = main(["Fix bug"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: OpenAI API error: Rate limit exceeded" in captured.err


@patch("timeless.cli.main.get_provider")
def test_main_unexpected_exception_hides_secrets(
    mock_get_provider: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    secret = "sk-secret-key-1234567890"
    mock_get_provider.side_effect = RuntimeError(f"Internal crash with {secret}")

    exit_code = main(["Fix bug"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error: An unexpected error occurred." in captured.err
    assert secret not in captured.err
    assert secret not in captured.out
