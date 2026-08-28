"""Thin LiteLLM wrapper for risk scoring.

Kept isolated so the rest of the app never imports litellm directly. If no
provider key is configured, or the call/parse fails, this returns None and the
caller falls back to heuristic scoring — so the pipeline always completes.

Providers are selected by the model name's prefix (see Settings.llm_provider):

    gpt-4o-mini                                  -> OpenAI    (OPENAI_API_KEY)
    groq/llama-3.1-8b-instant                    -> Groq      (GROQ_API_KEY)
    huggingface/meta-llama/Llama-3.1-8B-Instruct -> HF        (HUGGINGFACE_API_KEY)

Set CUSTODIAN_LLM_API_BASE to put a LiteLLM proxy in front of any of them.
"""

from __future__ import annotations

import json
import re

from .config import settings
from .models import Invoice

# System prompt: constrain the model to a strict JSON contract we can parse.
_SYSTEM_PROMPT = (
    "You are a bank's accounts-payable fraud & risk analyst. "
    "Assess the given invoice and respond with ONLY a JSON object of the form:\n"
    '{"risk_score": <int 0-100>, "fraud_flags": [<short strings>], '
    '"rationale": "<one or two sentences>"}\n'
    "Higher risk_score means more likely fraudulent or non-compliant. "
    "Consider: unusually large or round amounts, urgency language, mismatched "
    "or missing vendor account, back-dated or far-future dates, and vague line items."
)


def _build_user_prompt(invoice: Invoice) -> str:
    """Render the invoice into a compact, model-friendly description."""
    return (
        f"Invoice ID: {invoice.invoice_id}\n"
        f"Vendor: {invoice.vendor_name}\n"
        f"Vendor account: {invoice.vendor_account}\n"
        f"Amount: {invoice.amount} {invoice.currency}\n"
        f"Issued: {invoice.issue_date} | Due: {invoice.due_date}\n"
        f"Line items: {', '.join(invoice.line_items) or '(none)'}\n"
        f"Memo: {invoice.memo or '(none)'}"
    )


def _extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of a model response, tolerating extra prose."""
    # Fast path: the whole response is valid JSON.
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    # Fallback: grab the first {...} block and try again.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except ValueError:
        return None


def score_invoice_with_llm(invoice: Invoice) -> dict | None:
    """Ask an LLM (via LiteLLM) to score the invoice.

    Returns a dict with keys risk_score/fraud_flags/rationale, or None if the
    LLM is unavailable or the response can't be parsed.
    """
    if not settings.has_llm_credentials:
        return None

    try:
        import litellm
    except ImportError:
        return None

    # Route through a LiteLLM proxy/gateway when configured, else call the
    # provider directly. The key is chosen by the model's provider prefix, so a
    # "huggingface/*" model authenticates with the HF token rather than whatever
    # other provider key happens to be in the environment.
    extra: dict = {}
    if settings.llm_api_base:
        extra["api_base"] = settings.llm_api_base
    api_key = settings.llm_api_key or settings.llm_api_credential
    if api_key:
        extra["api_key"] = api_key

    try:
        response = litellm.completion(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(invoice)},
            ],
            temperature=0,  # deterministic scoring
            **extra,
        )
        content = response.choices[0].message.content or ""
    except Exception:
        # Network error, auth failure, rate limit, etc. — degrade gracefully.
        return None

    parsed = _extract_json(content)
    if not parsed or "risk_score" not in parsed:
        return None

    # Normalize into the shape the risk agent expects.
    return {
        "risk_score": int(parsed["risk_score"]),
        "fraud_flags": list(parsed.get("fraud_flags", [])),
        "rationale": str(parsed.get("rationale", "")),
    }
