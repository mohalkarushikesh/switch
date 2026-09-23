"""Risk agent: score an invoice for fraud/risk.

Scoring is a fall-through chain of three tiers, tried in order:

    1. local model  — on-device transformers model (offline, no cost), if
                       CUSTODIAN_LOCAL_MODEL is set;
    2. API LLM      — a provider via LiteLLM, if a key/base is configured;
    3. heuristic    — a transparent rule-based scorer that always succeeds.

The first tier to return a result wins, so the pipeline always produces an
assessment regardless of network, keys, or model availability.
"""

from __future__ import annotations

from ..config import settings
from ..llm import score_invoice_with_llm
from ..local_llm import score_invoice_locally
from ..models import Invoice, RiskAssessment


class RiskAgent:
    def assess(self, invoice: Invoice, llm_invoice: Invoice | None = None) -> RiskAssessment:
        """Return a RiskAssessment via the local -> API -> heuristic chain.

        llm_invoice, if given, is the PII-redacted view sent to any model; the
        heuristic path always scores the original invoice.
        """
        view = llm_invoice or invoice

        # Tier 1: on-device model (only when CUSTODIAN_LOCAL_MODEL is configured).
        local_result = score_invoice_locally(view)
        if local_result is not None:
            return self._from_model(local_result, source="local-llm")

        # Tier 2: API LLM via LiteLLM.
        llm_result = score_invoice_with_llm(view)
        if llm_result is not None:
            return self._from_model(llm_result, source="llm")

        # Tier 3: heuristic. Distinguish "no model was ever configured" from "a
        # model was configured but every tier failed" — otherwise a real outage
        # reads as 'no LLM configured' (the exact confusion a bad key caused).
        model_configured = bool(settings.local_model_path) or settings.has_llm_credentials
        return self._heuristic(invoice, llm_configured=model_configured)

    @staticmethod
    def _from_model(result: dict, source: str) -> RiskAssessment:
        """Build an assessment from a model tier's parsed result (score clamped)."""
        return RiskAssessment(
            risk_score=max(0, min(100, result["risk_score"])),
            fraud_flags=result["fraud_flags"],
            rationale=result["rationale"],
            source=source,
        )

    @staticmethod
    def _heuristic(invoice: Invoice, llm_configured: bool = False) -> RiskAssessment:
        """Simple, explainable scoring used when the LLM path doesn't produce a result.

        Each rule adds points and a flag; the total (capped at 100) is the score.
        llm_configured distinguishes a genuine LLM outage (True — a key is set but
        the call failed) from no LLM being configured at all (False).
        """
        score = 0
        flags: list[str] = []

        # Large amounts carry more inherent risk.
        if invoice.amount >= 50_000:
            score += 45
            flags.append("very large amount")
        elif invoice.amount >= 10_000:
            score += 25
            flags.append("large amount")

        # Suspiciously round amounts can indicate fabricated invoices.
        if invoice.amount >= 1_000 and invoice.amount % 1_000 == 0:
            score += 15
            flags.append("round amount")

        # Missing or malformed destination account.
        if not invoice.vendor_account or len(invoice.vendor_account) < 6:
            score += 30
            flags.append("missing/short vendor account")

        # Urgency language is a common social-engineering signal.
        memo = (invoice.memo or "").lower()
        if any(word in memo for word in ("urgent", "asap", "immediately", "wire now")):
            score += 20
            flags.append("urgency language in memo")

        # Vague or empty line items.
        if not invoice.line_items:
            score += 15
            flags.append("no line items")

        # Due date before issue date is a clear data-integrity problem.
        if invoice.due_date < invoice.issue_date:
            score += 25
            flags.append("due date precedes issue date")

        score = min(100, score)
        why = (
            "LLM configured but unavailable — call failed or returned no usable result"
            if llm_configured
            else "no LLM configured"
        )
        rationale = (
            f"Heuristic scoring ({why}). "
            + ("Flags: " + ", ".join(flags) + "." if flags else "No risk signals detected.")
        )
        return RiskAssessment(
            risk_score=score,
            fraud_flags=flags,
            rationale=rationale,
            source="heuristic",
        )
