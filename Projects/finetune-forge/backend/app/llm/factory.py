"""Build the configured LLM provider once and hand it to the app."""
from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.llm.azure_foundry import AzureFoundryProvider
from app.llm.base import LLMError, LLMProvider
from app.llm.mock import MockProvider


def build_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return MockProvider(system_prompt=settings.llm_system_prompt)
    if provider == "azure":
        return AzureFoundryProvider(
            endpoint=settings.azure_foundry_endpoint,
            deployment=settings.azure_foundry_deployment,
            api_key=settings.azure_foundry_api_key,
            api_version=settings.azure_foundry_api_version,
            system_prompt=settings.llm_system_prompt,
        )
    raise LLMError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")


@lru_cache
def get_provider() -> LLMProvider:
    return build_provider(get_settings())
