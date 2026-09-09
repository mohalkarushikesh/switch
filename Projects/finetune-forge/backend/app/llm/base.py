"""The provider interface every LLM backend implements.

Keeping the surface tiny (one async ``generate`` call plus a ``model`` label)
means the frontend and API never care which backend is wired in — mock today,
a fine-tuned Azure AI Foundry deployment tomorrow.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import ChatMessage


class LLMProvider(ABC):
    #: Short identifier surfaced in responses/health (e.g. "mock", "azure").
    name: str = "base"

    @property
    @abstractmethod
    def model(self) -> str:
        """Human-readable name of the underlying model / deployment."""

    @abstractmethod
    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Return the assistant's reply for the given conversation."""


class LLMError(RuntimeError):
    """Raised when a provider fails to produce a completion."""
