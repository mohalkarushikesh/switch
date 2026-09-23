"""Local (offline) LLM risk scorer — a `transformers` causal-LM run on-device.

This is the optional *first* tier of the scoring chain (local -> API -> heuristic).
Its point is to score with **no network and no API cost** — useful when the
provider is unreachable or keys are absent. On CPU a 0.5B model is seconds per
invoice, so it trades latency for independence; it is off unless
CUSTODIAN_LOCAL_MODEL points at a model directory.

Weights are loaded from a local path only (never downloaded here — the box has no
HF access), with transformers pinned offline. torch/transformers are imported
lazily so a deployment that doesn't use this tier never pays their import cost.
"""

from __future__ import annotations

import logging
import os

from .config import settings
from .llm import _SYSTEM_PROMPT, _build_user_prompt, _extract_json
from .models import Invoice

logger = logging.getLogger("custodian.local_llm")

# Loaded once on first use and reused (loading a 0.5B model is ~20s).
_MODEL = None
_TOKENIZER = None
_LOAD_FAILED = False

# Outcome tally, merged into /metrics alongside the API scorer's counts.
_LOCAL_COUNTS: dict[str, int] = {"local_success": 0, "local_failed": 0, "local_unparseable": 0}


def local_counts() -> dict[str, int]:
    """Snapshot of local-scorer outcomes since startup (for /metrics)."""
    return dict(_LOCAL_COUNTS)


def _load():
    """Load (and cache) the tokenizer+model from CUSTODIAN_LOCAL_MODEL. Returns
    (tokenizer, model) or (None, None) if unavailable — never raises."""
    global _MODEL, _TOKENIZER, _LOAD_FAILED
    if _MODEL is not None:
        return _TOKENIZER, _MODEL
    if _LOAD_FAILED or not settings.local_model_path:
        return None, None
    try:
        # No accidental network reach-out — this box can't hit HF anyway.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        torch.set_num_threads(os.cpu_count() or 4)
        path = settings.local_model_path
        logger.info("Loading local scoring model from %s …", path)
        _TOKENIZER = AutoTokenizer.from_pretrained(path)
        _MODEL = AutoModelForCausalLM.from_pretrained(path, dtype=torch.float32)
        logger.info("Local scoring model ready.")
        return _TOKENIZER, _MODEL
    except Exception as exc:
        logger.warning("Local model unavailable (%s): %s", type(exc).__name__, exc)
        _LOAD_FAILED = True  # don't retry a broken/missing path every invoice
        return None, None


def score_invoice_locally(invoice: Invoice) -> dict | None:
    """Score an invoice with the on-device model. Returns the risk dict, or None
    (no model configured, load failed, generation error, or unparseable output)."""
    if not settings.local_model_path:
        return None
    tokenizer, model = _load()
    if model is None:
        return None

    try:
        import torch

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(invoice)},
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=settings.local_model_max_tokens,
                do_sample=False,  # deterministic scoring
                pad_token_id=tokenizer.eos_token_id,
            )
        text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    except Exception as exc:
        logger.warning("Local scoring failed (%s): %s", type(exc).__name__, exc)
        _LOCAL_COUNTS["local_failed"] += 1
        return None

    parsed = _extract_json(text)
    if not parsed or "risk_score" not in parsed:
        logger.warning("Local model returned no usable JSON; deferring to next tier.")
        _LOCAL_COUNTS["local_unparseable"] += 1
        return None

    _LOCAL_COUNTS["local_success"] += 1
    return {
        "risk_score": int(parsed["risk_score"]),
        "fraud_flags": list(parsed.get("fraud_flags", [])),
        "rationale": str(parsed.get("rationale", "")),
    }
