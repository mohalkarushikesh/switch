"""Application configuration, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Which provider the LLM factory should build.
    llm_provider: str = "mock"

    # Comma-separated list of origins allowed by CORS.
    cors_origins: str = "http://localhost:5173"

    # Azure AI Foundry (used when llm_provider == "azure").
    azure_foundry_endpoint: str = ""
    azure_foundry_deployment: str = ""
    azure_foundry_api_key: str = ""
    azure_foundry_api_version: str = "2024-08-01-preview"

    # Generation defaults, shared across providers.
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512
    llm_system_prompt: str = (
        "You are FineTune Forge, a helpful assistant fine-tuned for this application."
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
