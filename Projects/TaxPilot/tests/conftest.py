"""Test configuration.

The whole suite runs offline and costs nothing: an autouse fixture makes every
`get_llm()` raise, so nodes and guardrails take their deterministic / fail-open
paths. Tests that want to exercise an LLM path inject a fake client explicitly.
"""

from __future__ import annotations

import pytest

import taxpilot.graph.nodes as nodes
import taxpilot.guardrails.pipeline as guardrails_pipeline
from taxpilot.observability import reset_degraded_log


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Force the no-LLM path everywhere a node or guardrail reaches for a model."""
    def _no_llm():
        raise RuntimeError("offline: no LLM configured in tests")

    monkeypatch.setattr(nodes, "get_llm", _no_llm)
    monkeypatch.setattr(guardrails_pipeline, "get_llm", _no_llm)
    reset_degraded_log()
    yield


@pytest.fixture
def sample_documents():
    from taxpilot.config import get_settings
    from taxpilot.intake import load_documents

    settings = get_settings()
    return load_documents(settings.absolute(settings.documents_dir))
