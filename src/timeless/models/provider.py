from abc import ABC, abstractmethod

from timeless.models.schemas import ModelResponse


class ModelProvider(ABC):
    """Abstract interface for model providers."""

    @abstractmethod
    def generate(self, prompt: str, model: str | None = None) -> ModelResponse:
        """Send a prompt to the provider and return a ModelResponse."""
        pass
