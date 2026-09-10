"""Heuristic extraction and deterministic normalization (the offline path)."""

from taxpilot.extraction import Extractor, to_deductions, to_income
from taxpilot.extraction.schema import canonicalize
from taxpilot.models import DocType, SourceDocument


def _form16():
    return SourceDocument(
        id="f16", filename="form16.txt", doc_type=DocType.FORM16,
        text=("FORM 16  Certificate under Section 203\n"
              "Employer: Acme Technologies Pvt Ltd\n"
              "Employee PAN: ABCDE1234F\n"
              "Gross salary: 14,00,000\n"
              "Total tax deducted: 1,20,000\n"),
    )


def test_canonicalize_prefers_specific_labels():
    assert canonicalize("Gross salary") == "gross_salary"
    assert canonicalize("Total tax deducted") == "tds"
    assert canonicalize("Interest income") == "interest_income"
    assert canonicalize("Interest paid during the year") == "amount"


def test_heuristic_extractor_reads_indian_amounts():
    result = Extractor(llm=None).extract(_form16())
    assert result.amount("gross_salary") == 14_00_000
    assert result.amount("tds") == 1_20_000
    # PAN stays a string, not mis-coerced to a number.
    assert result.field("pan").value == "ABCDE1234F"


def test_normalize_form16_to_income_with_tds():
    income = to_income([Extractor(llm=None).extract(_form16())])
    assert len(income) == 1
    assert income[0].kind == "salary"
    assert income[0].amount == 14_00_000
    assert income[0].withholding == 1_20_000


def test_rupee_prefixed_amount_is_parsed():
    doc = SourceDocument(
        id="80c", filename="80c.txt", doc_type=DocType.INVEST_80C,
        text="SECTION 80C INVESTMENT\nAmount invested: Rs 1,50,000\n",
    )
    candidates = to_deductions([Extractor(llm=None).extract(doc)])
    assert len(candidates) == 1
    assert candidates[0].citation.rule_id == "80C"
    assert candidates[0].amount == 1_50_000
    assert candidates[0].grounded is True


def test_rent_receipt_flags_review():
    doc = SourceDocument(
        id="rent", filename="rent.txt", doc_type=DocType.RENT_RECEIPT,
        text="RENT RECEIPT\nRent paid: 2,40,000\n",
    )
    candidates = to_deductions([Extractor(llm=None).extract(doc)])
    assert candidates[0].citation.rule_id == "HRA"
    assert candidates[0].needs_review is True


def test_form16a_carries_tds_without_income():
    doc = SourceDocument(
        id="f16a", filename="form16a.txt", doc_type=DocType.FORM16A,
        text="FORM 16A\nTotal tax deducted: 5,000\n",
    )
    income = to_income([Extractor(llm=None).extract(doc)])
    assert sum(i.withholding for i in income) == 5_000
