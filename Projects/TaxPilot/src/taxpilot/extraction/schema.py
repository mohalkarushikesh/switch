"""Field and document catalogs shared by extraction, normalization and research.

The LLM extractor and the offline heuristic extractor both emit (label, value)
pairs; `canonicalize` folds either one's labels onto the same field names.
`INCOME_MAP` and `DEDUCTION_DOCS` are the deterministic bridge from documents to
engine inputs - mapping a Form 16 to salary + TDS, or an 80C proof to a Chapter
VI-A deduction, is settled structure, not a judgement for a model, so it lives
here in plain code.
"""

from __future__ import annotations

from taxpilot.models import DeductionKind, DocType

#: Ordered (label-substring -> canonical field). First match wins, so specific
#: phrases precede generic ones.
_LABEL_ALIASES: list[tuple[str, str]] = [
    ("gross salary", "gross_salary"),
    ("income chargeable under the head salaries", "gross_salary"),
    ("total tax deducted", "tds"),
    ("tax deducted at source", "tds"),
    ("tax deducted", "tds"),
    ("tds", "tds"),
    ("interest income", "interest_income"),
    ("interest earned", "interest_income"),
    ("interest paid", "amount"),          # home-loan interest -> a deduction amount
    ("amount invested", "amount"),
    ("premium", "amount"),
    ("donation amount", "amount"),
    ("rent paid", "amount"),
    ("amount", "amount"),
    ("employer", "payer"),
    ("deductor", "payer"),
    ("lender", "payer"),
    ("insurer", "payer"),
    ("institution", "payer"),
    ("bank", "payer"),
    ("payer", "payer"),
    ("pan", "pan"),
    ("age category", "age_category"),
    ("tax regime", "regime"),
    ("residential status", "residential_status"),
]


def canonicalize(label: str) -> str:
    lowered = label.strip().lower()
    for needle, canonical in _LABEL_ALIASES:
        if needle in lowered:
            return canonical
    return lowered.replace(" ", "_")


#: doc_type -> {income fields as (canonical_field, income_kind), TDS field}.
INCOME_MAP: dict[DocType, dict] = {
    DocType.FORM16: {"income": [("gross_salary", "salary")], "withholding": "tds"},
    DocType.INTEREST_CERT: {"income": [("interest_income", "interest")], "withholding": "tds"},
    # Form 16A carries TDS on non-salary income but no income line of its own.
    DocType.FORM16A: {"income": [], "withholding": "tds"},
    # Form 26AS is a reconciliation source (used by the audit scorer), deliberately
    # NOT summed into TDS here - otherwise its totals would double-count Form 16.
}

#: doc_type -> (rule_id, kind, display name, needs_review, amount field).
DEDUCTION_DOCS: dict[DocType, tuple[str, DeductionKind, str, bool, str]] = {
    DocType.INVEST_80C: ("80C", DeductionKind.CHAPTER_VIA, "Section 80C investment",
                         False, "amount"),
    DocType.MEDICAL_80D: ("80D", DeductionKind.CHAPTER_VIA, "Section 80D health insurance",
                          False, "amount"),
    DocType.DONATION_80G: ("80G", DeductionKind.CHAPTER_VIA, "Section 80G donation",
                           False, "amount"),
    DocType.HOME_LOAN: ("SEC24B", DeductionKind.HOUSE_PROPERTY, "Home-loan interest (Sec 24(b))",
                        False, "amount"),
    # HRA depends on the salary break-up and actual rent, which a receipt cannot
    # establish - always send it to a human.
    DocType.RENT_RECEIPT: ("HRA", DeductionKind.SALARY_EXEMPTION, "HRA exemption (Sec 10(13A))",
                           True, "amount"),
}
