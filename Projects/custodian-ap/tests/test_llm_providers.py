"""Provider selection for LLM risk scoring — offline.

Covers the model-prefix -> provider -> API-key mapping, the CUSTODIAN_DISABLE_LLM
kill-switch, and that the resolved key is actually handed to LiteLLM. `litellm`
is stubbed in sys.modules, so nothing here touches the network.
"""

from __future__ import annotations

import sys
from datetime import date
from types import SimpleNamespace

import pytest

from custodian import llm as llm_module
from custodian.config import load_settings
from custodian.models import Invoice

# Every provider credential the config reads; cleared so a developer's .env
# (loaded into os.environ when custodian.config was imported) can't leak in.
_CREDENTIAL_VARS = (
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "HUGGINGFACE_API_KEY",
    "HF_TOKEN",
    "CUSTODIAN_LLM_API_BASE",
    "CUSTODIAN_LLM_API_KEY",
    "CUSTODIAN_DISABLE_LLM",
)


def settings_with(monkeypatch, **env):
    """A fresh Settings with only the given credential/model env vars set."""
    for var in _CREDENTIAL_VARS:
        monkeypatch.delenv(var, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return load_settings()


@pytest.fixture
def invoice() -> Invoice:
    return Invoice(
        invoice_id="INV-LLM-1",
        vendor_name="Globex Corp",
        vendor_account="GLBX-CHK-4521",
        amount=4200.0,
        issue_date=date(2026, 8, 14),
        due_date=date(2026, 9, 14),
        line_items=["Cloud hosting"],
        memo="Monthly services",
    )


# --- provider resolution ---------------------------------------------------

@pytest.mark.parametrize(
    "model, expected",
    [
        ("gpt-4o-mini", "openai"),                                  # bare = OpenAI
        ("groq/llama-3.1-8b-instant", "groq"),
        ("huggingface/meta-llama/Llama-3.1-8B-Instruct", "huggingface"),
        ("huggingface/hf-inference/mistralai/Mistral-7B-Instruct-v0.3", "huggingface"),
        ("meta-llama/Llama-3.1-8B-Instruct", "openai"),             # unknown prefix
    ],
)
def test_llm_provider_from_model_prefix(monkeypatch, model, expected):
    assert settings_with(monkeypatch, CUSTODIAN_LLM_MODEL=model).llm_provider == expected


def test_hf_token_is_picked_up_from_either_env_var(monkeypatch):
    model = "huggingface/meta-llama/Llama-3.1-8B-Instruct"
    primary = settings_with(monkeypatch, CUSTODIAN_LLM_MODEL=model, HUGGINGFACE_API_KEY="hf_aaa")
    assert primary.llm_api_credential == "hf_aaa"
    assert primary.has_llm_credentials is True

    # HF_TOKEN is what `huggingface-cli login` writes, so it's accepted too.
    fallback = settings_with(monkeypatch, CUSTODIAN_LLM_MODEL=model, HF_TOKEN="hf_bbb")
    assert fallback.llm_api_credential == "hf_bbb"
    assert fallback.has_llm_credentials is True


def test_credential_must_match_the_models_provider(monkeypatch):
    """An OpenAI key does not make a huggingface/* model reachable."""
    s = settings_with(
        monkeypatch,
        CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
        OPENAI_API_KEY="sk-openai",
    )
    assert s.llm_api_credential is None
    assert s.has_llm_credentials is False


def test_gateway_base_url_is_enough_without_a_provider_key(monkeypatch):
    s = settings_with(
        monkeypatch,
        CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
        CUSTODIAN_LLM_API_BASE="http://litellm:4000",
    )
    assert s.has_llm_credentials is True


# --- kill-switch -----------------------------------------------------------

def test_disable_llm_overrides_a_present_key(monkeypatch):
    s = settings_with(
        monkeypatch,
        CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
        HUGGINGFACE_API_KEY="hf_aaa",
        CUSTODIAN_DISABLE_LLM="1",
    )
    assert s.disable_llm is True
    assert s.has_llm_credentials is False


def test_disabled_scorer_makes_no_call(monkeypatch, invoice):
    """With the kill-switch on, litellm is never even imported."""
    def explode(*_args, **_kwargs):
        raise AssertionError("litellm must not be called when the LLM is disabled")

    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(completion=explode))
    monkeypatch.setattr(
        llm_module,
        "settings",
        settings_with(
            monkeypatch,
            CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
            HUGGINGFACE_API_KEY="hf_aaa",
            CUSTODIAN_DISABLE_LLM="1",
        ),
    )
    assert llm_module.score_invoice_with_llm(invoice) is None


# --- the key actually reaches LiteLLM -------------------------------------

def _stub_litellm(monkeypatch, content: str) -> list[dict]:
    """Install a fake `litellm`; returns the list its completion() kwargs land in."""
    calls: list[dict] = []
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )

    def completion(**kwargs):
        calls.append(kwargs)
        return response

    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(completion=completion))
    return calls


def test_hf_token_is_passed_to_litellm(monkeypatch, invoice):
    calls = _stub_litellm(
        monkeypatch,
        '{"risk_score": 62, "fraud_flags": ["changed bank details"], "rationale": "Vendor account differs."}',
    )
    monkeypatch.setattr(
        llm_module,
        "settings",
        settings_with(
            monkeypatch,
            CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
            HUGGINGFACE_API_KEY="hf_aaa",
        ),
    )

    result = llm_module.score_invoice_with_llm(invoice)

    assert result == {
        "risk_score": 62,
        "fraud_flags": ["changed bank details"],
        "rationale": "Vendor account differs.",
    }
    assert len(calls) == 1
    assert calls[0]["model"] == "huggingface/meta-llama/Llama-3.1-8B-Instruct"
    assert calls[0]["api_key"] == "hf_aaa"
    assert "api_base" not in calls[0]          # direct call, no gateway configured


def test_gateway_key_wins_over_the_provider_key(monkeypatch, invoice):
    """When a LiteLLM proxy is configured, its master key authenticates the call."""
    calls = _stub_litellm(monkeypatch, '{"risk_score": 10, "fraud_flags": [], "rationale": "ok"}')
    monkeypatch.setattr(
        llm_module,
        "settings",
        settings_with(
            monkeypatch,
            CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
            HUGGINGFACE_API_KEY="hf_aaa",
            CUSTODIAN_LLM_API_BASE="http://litellm:4000",
            CUSTODIAN_LLM_API_KEY="sk-proxy",
        ),
    )

    assert llm_module.score_invoice_with_llm(invoice)["risk_score"] == 10
    assert calls[0]["api_base"] == "http://litellm:4000"
    assert calls[0]["api_key"] == "sk-proxy"


def test_unparseable_response_falls_back(monkeypatch, invoice):
    _stub_litellm(monkeypatch, "I cannot assess this invoice.")
    monkeypatch.setattr(
        llm_module,
        "settings",
        settings_with(
            monkeypatch,
            CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
            HUGGINGFACE_API_KEY="hf_aaa",
        ),
    )
    assert llm_module.score_invoice_with_llm(invoice) is None


def test_provider_error_falls_back(monkeypatch, invoice):
    """A 401/rate-limit/network error must degrade to the heuristic, not raise."""
    def boom(**_kwargs):
        raise RuntimeError("401 Unauthorized: invalid HF token")

    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(completion=boom))
    monkeypatch.setattr(
        llm_module,
        "settings",
        settings_with(
            monkeypatch,
            CUSTODIAN_LLM_MODEL="huggingface/meta-llama/Llama-3.1-8B-Instruct",
            HUGGINGFACE_API_KEY="hf_aaa",
        ),
    )
    assert llm_module.score_invoice_with_llm(invoice) is None
