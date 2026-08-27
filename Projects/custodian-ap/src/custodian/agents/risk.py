"""Risk agent: score an invoice for fraud/risk.

Primary path uses an LLM via LiteLLM. If that's unavailable (no API key,
network error, unparseable response), it falls back to a transparent
rule-based heuristic so the pipeline always produces an assessment.
"""

from __future__ import annotations

from ..llm import score_invoice_with_llm
from ..models import Invoice, RiskAssessment


class RiskAgent:
    def assess(self, invoice: Invoice, llm_invoice: Invoice | None = None) -> RiskAssessment:
        """Return a RiskAssessment, preferring the LLM and falling back to rules.

        llm_invoice, if given, is the PII-redacted view sent to the LLM; the
        heuristic path always scores the original invoice.
        """
        llm_result = score_invoice_with_llm(llm_invoice or invoice)
        if llm_result is not None:
            score = max(0, min(100, llm_result["risk_score"]))  # clamp to 0-100
            return RiskAssessment(
                risk_score=score,
                fraud_flags=llm_result["fraud_flags"],
                rationale=llm_result["rationale"],
                source="llm",
            )
        return self._heuristic(invoice)

    @staticmethod
    def _heuristic(invoice: Invoice) -> RiskAssessment:
        """Simple, explainable scoring used when no LLM is available.

        Each rule adds points and a flag; the total (capped at 100) is the score.
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
        rationale = (
            "Heuristic scoring (no LLM configured). "
            + ("Flags: " + ", ".join(flags) + "." if flags else "No risk signals detected.")
        )
        return RiskAssessment(
            risk_score=score,
            fraud_flags=flags,
            rationale=rationale,
            source="heuristic",
        )
