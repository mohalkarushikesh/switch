"""Test isolation.

Settings normally read the project's `.env`, which would make the offline suite
depend on whatever the developer has configured locally. Detaching the env file
at import time (before any test module builds a Settings object) keeps the
defaults in `config.py` as the single source of truth for tests.
"""

from __future__ import annotations

import os

import pytest

from advanced_rag.config import Settings, get_settings

Settings.model_config["env_file"] = None

# Guardrail and graph tests must never reach the network. A placeholder key lets
# the Anthropic client construct without complaining; the fakes intercept the
# calls, and anything that slips past fails loudly instead of billing.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """`get_settings` is lru_cached; drop it between tests that patch settings."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
