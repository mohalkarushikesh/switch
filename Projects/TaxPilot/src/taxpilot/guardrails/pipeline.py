"""The guardrails pipeline.

Inbound (document submission)          Outbound (drafted report)
  1. shape        (present, bounded)     4. figure_integrity  (no invented rupee figure)
  2. injection    (block)                5. citation_grounding (deduction cites a real section)
  3. pii_inventory(catalogue)            6. pii_redaction     (mask PAN/Aadhaar for display)
                                         7. disclaimer        (annotate: draft, not filed)
  (intake_review, LLM, block)            8. output_review     (LLM grounding + safety)

Layer 4 is the one that matters most, and it is deliberately deterministic: every
rupee figure in the narrative must be one the engine computed, a published
constant, or a grounded deduction amount. That is how "the model never decides a
number" stops being a hope and becomes an enforced invariant.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from taxpilot.calc import brackets as B
from taxpilot.config import Settings, get_settings
from taxpilot.guardrails import patterns
from taxpilot.knowledge.rules import is_known
from taxpilot.llm import prompts
from taxpilot.llm.client import LLMClient, get_llm
from taxpilot.models import DeductionCandidate, GuardrailOutcome, SourceDocument, TaxReturn
from taxpilot.money import rupees

logger = logging.getLogger(__name__)

MAX_TOTAL_CHARS = 200_000
#: A rupee figure below this in the narrative is ignored by figure_integrity - it
#: is almost always a count or a footnote, not a fabricated tax figure.
FIGURE_MIN = 100

_DISCLAIMER = (
    "\n\n---\n_This is a draft return prepared for review by a qualified tax "
    "professional. It has not been filed and is not tax advice._"
)


def _published_constants() -> set[int]:
    """Rupee figures a correct explanation may legitimately cite (from the engine's
    own constants), so citing "the ₹1,50,000 80C ceiling" is allowed while an
    otherwise-unexplained number is treated as invented."""
    values: set[int] = {0}
    for lo, _ in B.NEW_REGIME_SLABS_2024:
        values.add(lo)
    for schedule in B.OLD_REGIME_SLABS_2024.values():
        for lo, _ in schedule:
            values.add(lo)
    values.update({
        B.STANDARD_DEDUCTION_NEW_2024, B.STANDARD_DEDUCTION_OLD_2024,
        B.REBATE_87A_NEW_THRESHOLD, B.REBATE_87A_NEW_CAP,
        B.REBATE_87A_OLD_THRESHOLD, B.REBATE_87A_OLD_CAP,
        B.CAP_80C, B.CAP_80CCD1B, B.CAP_80D_BELOW_60, B.CAP_80D_SENIOR,
        B.CAP_80TTA, B.CAP_80TTB, B.CAP_SEC24B,
    })
    for threshold, _ in B.SURCHARGE_BANDS:
        values.add(threshold)
    return {v for v in values if v}


_CONSTANTS = _published_constants()


class IntakeVerdict(BaseModel):
    is_tax_documents: bool = Field(description="true if this is a genuine tax-document submission")
    reason: str = Field(description="one sentence")


class OutputVerdict(BaseModel):
    safe: bool = Field(description="true if the draft may be shown as written")
    issue: str = Field(description="what to fix, or 'none'")


class GuardrailResult(BaseModel):
    outcomes: list[GuardrailOutcome] = Field(default_factory=list)
    text: str = ""
    blocked: bool = False
    message: str = ""

    def record(self, outcome: GuardrailOutcome) -> None:
        self.outcomes.append(outcome)
        if outcome.action == "block":
            self.blocked = True
            self.message = f"Stopped by the {outcome.layer} guardrail: {outcome.detail}"


class Guardrails:
    def __init__(self, settings: Settings | None = None, llm: LLMClient | None = None) -> None:
        self.settings = settings or get_settings()
        self._llm = llm

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    # ------------------------------------------------------------- inbound

    def check_documents(
        self, documents: list[SourceDocument], *, use_llm: bool = True
    ) -> GuardrailResult:
        result = GuardrailResult()
        if not self.settings.enable_guardrails:
            return result

        if not documents:
            result.record(_block("shape", "no documents were submitted"))
            return result
        total = sum(len(d.text) for d in documents)
        if total > MAX_TOTAL_CHARS:
            result.record(_block("shape", f"submission exceeds {MAX_TOTAL_CHARS} characters"))
            return result
        result.record(GuardrailOutcome(layer="shape", passed=True,
                                       detail=f"{len(documents)} documents, {total} chars"))

        for doc in documents:
            hits = patterns.find_injections(doc.text)
            if hits:
                result.record(_block(
                    "injection",
                    f"{doc.filename} contains text steering the assistant: {hits[0]!r}",
                ))
                return result
        result.record(GuardrailOutcome(layer="injection", passed=True, detail="no steering text"))

        # PII inventory - non-blocking: tax documents are full of PANs and Aadhaar
        # by nature; the point is to know they are there so the outbound redaction
        # layer can mask them.
        kinds = sorted({k for d in documents for k in patterns.inventory_pii(d.text)})
        result.record(GuardrailOutcome(
            layer="pii_inventory", passed=True,
            detail=("found " + ", ".join(kinds)) if kinds else "no PII detected",
        ))

        if not use_llm:
            return result

        summary = "\n".join(f"- {d.filename} ({d.doc_type.value}): {d.preview(200)}"
                            for d in documents)
        verdict = self._classify(IntakeVerdict, prompts.GUARDRAIL_INTAKE_SYSTEM, summary, "intake")
        if verdict is None:
            result.record(_skipped("intake_review", "classifier unavailable"))
        elif not verdict.is_tax_documents:
            result.record(_block("intake_review",
                                 verdict.reason or "not a tax-document submission"))
        else:
            result.record(GuardrailOutcome(layer="intake_review", passed=True, detail="tax docs"))
        return result

    # ------------------------------------------------------------ outbound

    def check_output(
        self,
        report: str,
        tax_return: TaxReturn | None,
        deductions: list[DeductionCandidate] | None = None,
        *,
        use_llm: bool = True,
    ) -> GuardrailResult:
        result = GuardrailResult(text=report)
        if not self.settings.enable_guardrails:
            return result

        # Layer 4 - figure integrity. THE invariant: no invented numbers.
        allowed = _CONSTANTS | (tax_return.line_amounts() if tax_return else set())
        allowed |= {abs(c.amount) for c in (deductions or [])}
        invented = sorted(
            a for a in patterns.rupee_amounts(report) if a >= FIGURE_MIN and a not in allowed
        )
        if invented:
            result.record(_block(
                "figure_integrity",
                "the narrative states rupee figures the engine did not compute: "
                + ", ".join(rupees(a) for a in invented[:5]),
            ))
        else:
            result.record(GuardrailOutcome(layer="figure_integrity", passed=True,
                                           detail="all figures trace to the engine"))

        # Layer 5 - citation grounding.
        ungrounded = [
            c for c in (deductions or [])
            if not c.grounded or not is_known(c.citation.rule_id)
        ]
        if ungrounded:
            result.record(_block(
                "citation_grounding",
                "deduction(s) without a valid section citation: "
                + ", ".join(c.name for c in ungrounded[:5]),
            ))
        else:
            result.record(GuardrailOutcome(layer="citation_grounding", passed=True,
                                           detail=f"{len(deductions or [])} deductions grounded"))

        # Layer 6 - PII redaction for display.
        redacted, pii = patterns.redact_pii(result.text)
        result.text = redacted
        result.record(GuardrailOutcome(
            layer="pii_redaction", passed=True,
            action="redact" if pii else "allow",
            detail=("masked " + ", ".join(pii)) if pii else "no PII in report",
        ))

        # Layer 7 - disclaimer.
        if "not tax advice" not in result.text.lower():
            result.text = result.text.rstrip() + _DISCLAIMER
            result.record(GuardrailOutcome(layer="disclaimer", passed=True, action="annotate",
                                           detail="appended draft/not-advice disclaimer"))
        else:
            result.record(GuardrailOutcome(layer="disclaimer", passed=True, detail="present"))

        if not use_llm:
            return result

        # Layer 8 - LLM output review.
        prompt = ("Computed figures the narrative may use:\n"
                  + (", ".join(rupees(a) for a in sorted(allowed) if a) if tax_return else "(none)")
                  + "\n\nDraft report:\n" + result.text)
        verdict = self._classify(OutputVerdict, prompts.OUTPUT_REVIEW_SYSTEM, prompt, "output")
        if verdict is None:
            result.record(_skipped("output_review", "reviewer unavailable"))
        elif not verdict.safe:
            result.record(_block("output_review", verdict.issue or "failed safety review"))
        else:
            result.record(GuardrailOutcome(layer="output_review", passed=True, detail="approved"))
        return result

    # -------------------------------------------------------------- private

    def _classify(self, schema, system: str, text: str, label: str):
        try:
            return self.llm.complete_json(text, schema, system=system, effort="low")
        except Exception:
            logger.warning("Guardrail layer %s failed open", label)
            return None


def _block(layer: str, detail: str) -> GuardrailOutcome:
    logger.warning("Guardrail %s blocked: %s", layer, detail)
    return GuardrailOutcome(layer=layer, passed=False, action="block", detail=detail)


def _skipped(layer: str, detail: str) -> GuardrailOutcome:
    logger.warning("Guardrail %s did not run: %s", layer, detail)
    return GuardrailOutcome(layer=layer, passed=False, action="skip", detail=detail)


_guardrails: Guardrails | None = None


def get_guardrails() -> Guardrails:
    global _guardrails
    if _guardrails is None:
        _guardrails = Guardrails()
    return _guardrails
