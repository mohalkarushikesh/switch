"""Shared data models used across intake, extraction, the knowledge base, the
deterministic engine, the audit scorer, the graph and the API.

This is an Indian income-tax copilot (FY 2024-25 / AY 2025-26). Money is carried
as whole rupees (integers) everywhere past extraction - returns are rounded to the
rupee, and integer arithmetic keeps the engine's totals exactly reproducible,
which is what makes "the number is traceable" a testable claim.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocType(StrEnum):
    """Kinds of source document the intake agent routes on."""

    FORM16 = "form16"           # salary + TDS (employer)
    FORM16A = "form16a"         # TDS on non-salary income
    FORM26AS = "form26as"       # consolidated TDS statement (used for reconciliation)
    INTEREST_CERT = "interest_cert"
    RENT_RECEIPT = "rent_receipt"       # HRA (Section 10(13A))
    INVEST_80C = "invest_80c"           # LIC / PPF / ELSS proofs
    MEDICAL_80D = "medical_80d"         # health-insurance premium
    DONATION_80G = "donation_80g"
    HOME_LOAN = "home_loan"             # interest certificate (Section 24(b))
    OTHER = "other"


class AgeCategory(StrEnum):
    """Age band on the last day of the year - it sets the basic exemption limit."""

    BELOW_60 = "below_60"
    SENIOR = "senior"            # 60 to under 80
    SUPER_SENIOR = "super_senior"  # 80+


class Regime(StrEnum):
    OLD = "old"
    NEW = "new"


class DeductionKind(StrEnum):
    """Where a deduction lands in the computation."""

    CHAPTER_VIA = "chapter_via"          # 80C, 80D, 80CCD(1B), 80TTA/TTB, 80G ...
    HOUSE_PROPERTY = "house_property"    # Section 24(b) home-loan interest set-off
    SALARY_EXEMPTION = "salary_exemption"  # HRA (Section 10(13A)) and similar


# --------------------------------------------------------------------- sources


class SourceDocument(BaseModel):
    """One uploaded document plus its extracted text and provenance."""

    id: str
    filename: str
    doc_type: DocType = DocType.OTHER
    text: str
    #: OCR confidence when the text came from an image; None for born-digital text.
    ocr_confidence: float | None = None

    def preview(self, limit: int = 400) -> str:
        return self.text[:limit]


# ------------------------------------------------------------------ extraction


class ExtractedField(BaseModel):
    """One field pulled from a document, with the model's confidence in it."""

    name: str
    value: float | str
    confidence: float = Field(ge=0.0, le=1.0)
    source_doc: str
    box: str = ""


class ExtractionResult(BaseModel):
    doc_id: str
    doc_type: DocType
    fields: list[ExtractedField] = Field(default_factory=list)

    def field(self, name: str) -> ExtractedField | None:
        return next((f for f in self.fields if f.name == name), None)

    def amount(self, name: str, default: float = 0.0) -> float:
        found = self.field(name)
        if found is None or isinstance(found.value, str):
            return default
        return float(found.value)


# ------------------------------------------------------------ normalized inputs


class IncomeItem(BaseModel):
    """A normalized income line the engine can consume directly."""

    #: salary | interest | other
    kind: str
    amount: int
    payer: str = ""
    source_doc: str = ""
    #: Tax already deducted at source (TDS) against this item.
    withholding: int = 0


class TaxpayerProfile(BaseModel):
    """The classifier's structured read of who is filing."""

    age_category: AgeCategory = AgeCategory.BELOW_60
    residential_status: Literal["resident", "non_resident"] = "resident"
    #: "auto" makes the engine compute both regimes and keep the lower tax.
    regime_preference: Literal["auto", "old", "new"] = "auto"


class Citation(BaseModel):
    """A pointer to the authority behind a figure or a proposed deduction.

    `rule_id` is the join key into the rule catalog (knowledge/rules.py); it is
    what the grounding guardrail checks, so a citation the corpus does not know
    about cannot survive to the report.
    """

    rule_id: str
    source: str = ""       # e.g. "Income-tax Act, 1961"
    section: str = ""      # e.g. "Section 80C"

    def label(self) -> str:
        where = self.source or self.rule_id
        return f"{where} - {self.section}" if self.section else where


class DeductionCandidate(BaseModel):
    """A deduction the researcher proposes, grounded in a rule."""

    name: str
    kind: DeductionKind
    amount: int
    citation: Citation
    rationale: str = ""
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    #: Set when the proposal needs a human to confirm eligibility or the amount.
    needs_review: bool = False
    #: Cleared by the grounding check when the citation resolves to a real rule.
    grounded: bool = False


# --------------------------------------------------------------- computed return


class TaxLine(BaseModel):
    """One line of the computed return, carrying the rule it came from."""

    line: str
    label: str
    amount: int
    citation: Citation | None = None


class TaxReturn(BaseModel):
    """The deterministic engine's output. No field here was produced by an LLM."""

    tax_year: int
    regime: Regime = Regime.NEW

    gross_total_income: int = 0
    deductions_total: int = 0
    total_income: int = 0            # taxable income

    tax_before_rebate: int = 0
    rebate_87a: int = 0
    surcharge: int = 0
    cess: int = 0
    total_tax: int = 0

    tds: int = 0                     # taxes already paid (deducted at source)
    #: Positive = refund owed to the taxpayer; negative = balance payable.
    refund_or_due: int = 0

    #: The other regime's total tax, so the regime choice is auditable.
    alternative_regime_tax: int = 0

    lines: list[TaxLine] = Field(default_factory=list)

    def line_amounts(self) -> set[int]:
        amounts = {
            self.gross_total_income, self.deductions_total, self.total_income,
            self.tax_before_rebate, self.rebate_87a, self.surcharge, self.cess,
            self.total_tax, self.tds, self.refund_or_due, abs(self.refund_or_due),
            self.alternative_regime_tax,
        }
        amounts.update(line.amount for line in self.lines)
        return {a for a in amounts if a}


# --------------------------------------------------------------------- audit


class RiskFlag(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    weight: int
    detail: str
    evidence: str = ""


class AuditRisk(BaseModel):
    score: int = 0
    band: Literal["low", "medium", "high"] = "low"
    flags: list[RiskFlag] = Field(default_factory=list)


# ------------------------------------------------------------ review + guardrails


class ReviewItem(BaseModel):
    reason: str
    area: str          # "extraction" | "deduction" | "audit" | "amount"
    detail: str = ""


class Correction(BaseModel):
    """A human edit applied on resume. Kept for the feedback log."""

    #: "regime" | "deduction_drop" | "age_category" | "note"
    target: str
    value: Any = None
    note: str = ""


class GuardrailOutcome(BaseModel):
    """Result of one guardrail layer.

    `passed` means the layer ran *and* cleared the content. A layer that could not
    run reports action="skip" with passed=False: it did not block, but it vetted
    nothing, and calling that a pass overstates the scrutiny the return received.
    """

    layer: str
    passed: bool
    action: Literal["allow", "redact", "annotate", "block", "skip"] = "allow"
    detail: str = ""

    @property
    def ran(self) -> bool:
        return self.action != "skip"


class TraceStep(BaseModel):
    node: str
    detail: str = ""
    elapsed_ms: int = 0


# --------------------------------------------------------------------- response


class ReturnResponse(BaseModel):
    """What the API returns for a prepared (or paused) return."""

    tax_year: int
    regime: Regime = Regime.NEW
    tax_return: TaxReturn | None = None
    audit: AuditRisk | None = None
    report: str = ""
    #: A short plain-language summary written by the LLM. Empty when the run was
    #: deterministic (no model), which is how the UI shows the difference.
    llm_summary: str = ""
    #: Whether this run used the model at all. The UI shows the AI summary only when
    #: True, and a "deterministic engine only" note otherwise.
    used_llm: bool = True
    citations: list[Citation] = Field(default_factory=list)

    awaiting_review: bool = False
    review_items: list[ReviewItem] = Field(default_factory=list)
    thread_id: str | None = None

    guardrails: list[GuardrailOutcome] = Field(default_factory=list)
    blocked: bool = False
    block_message: str = ""

    trace: list[TraceStep] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
