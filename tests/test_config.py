import os
from pathlib import Path

import pytest

from timeless.config import Config, load_config, resolve_api_key, save_config


def test_config_save_and_load(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.json"
    cfg = Config(
        default_provider="anthropic",
        openai_api_key="sk-test-openai",
        anthropic_api_key="sk-test-anthropic",
    )

    save_config(cfg, cfg_file)
    assert cfg_file.exists()

    # Check file permissions on Unix
    if hasattr(os, "stat"):
        mode = os.stat(cfg_file).st_mode & 0o777
        assert mode == 0o600

    loaded = load_config(cfg_file)
    assert loaded.default_provider == "anthropic"
    assert loaded.openai_api_key == "sk-test-openai"
    assert loaded.anthropic_api_key == "sk-test-anthropic"


def test_resolve_api_key_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_file = tmp_path / "config.json"
    cfg = Config(openai_api_key="cfg-key")
    save_config(cfg, cfg_file)

    # 1. Explicit key overrides all
    key = resolve_api_key("openai", explicit_key="explicit-key", config_path=cfg_file)
    assert key == "explicit-key"

    # 2. Env var overrides config file
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    key = resolve_api_key("openai", config_path=cfg_file)
    assert key == "env-key"

    # 3. Config file fallback when env var unset
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    key = resolve_api_key("openai", config_path=cfg_file)
    assert key == "cfg-key"
