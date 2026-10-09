import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "timeless"
CONFIG_FILE = CONFIG_DIR / "config.json"

ENV_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


@dataclass
class Config:
    default_provider: str = "openai"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_provider": self.default_provider,
            "openai_api_key": self.openai_api_key,
            "anthropic_api_key": self.anthropic_api_key,
            "gemini_api_key": self.gemini_api_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        return cls(
            default_provider=data.get("default_provider", "openai"),
            openai_api_key=data.get("openai_api_key"),
            anthropic_api_key=data.get("anthropic_api_key"),
            gemini_api_key=data.get("gemini_api_key"),
        )


def load_config(config_path: Path = CONFIG_FILE) -> Config:
    if not config_path.is_file():
        return Config()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return Config.from_dict(data)
    except Exception:
        return Config()


def save_config(config: Config, config_path: Path = CONFIG_FILE) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(config.to_dict(), indent=2)
    config_path.write_text(content, encoding="utf-8")
    try:
        os.chmod(config_path, 0o600)
    except OSError:
        pass


def resolve_api_key(
    provider_name: str,
    explicit_key: str | None = None,
    config_path: Path = CONFIG_FILE,
) -> str | None:
    """Resolve API key: explicit > env var > config file."""
    if explicit_key:
        return explicit_key

    provider = provider_name.lower().strip()
    if provider in ("anthropic", "claude"):
        provider = "anthropic"
    elif provider in ("gemini", "google"):
        provider = "gemini"

    env_var = ENV_KEY_MAP.get(provider)
    if env_var:
        env_val = os.environ.get(env_var)
        if env_val:
            return env_val
        if provider == "gemini":
            fallback = os.environ.get("GOOGLE_API_KEY")
            if fallback:
                return fallback

    cfg = load_config(config_path)
    if provider == "openai":
        return cfg.openai_api_key
    elif provider == "anthropic":
        return cfg.anthropic_api_key
    elif provider == "gemini":
        return cfg.gemini_api_key

    return None
