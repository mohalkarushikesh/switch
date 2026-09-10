"""The audit scorer is deterministic, so each flag is tested directly."""

from taxpilot.audit import score_return
from taxpilot.calc import compute
from taxpilot.models import (
    Citation,
    DeductionCandidate,
    DeductionKind,
    DocType,
    ExtractedField,
    ExtractionResult,
    IncomeItem,
    TaxpayerProfile,
)


def _ded(rule_id, amount, kind=DeductionKind.CHAPTER_VIA, needs_review=False):
    return DeductionCandidate(name=rule_id, kind=kind, amount=amount,
                              citation=Citation(rule_id=rule_id), grounded=True,
                              needs_review=needs_review)


def test_clean_return_is_low_risk():
    income = [IncomeItem(kind="salary", amount=800_000, withholding=40_000)]
    ret = compute(TaxpayerProfile(regime_preference="new"), income)
    audit = score_return(ret, income, [], [])
    assert audit.band == "low"


def test_tds_exceeding_26as_is_flagged_high():
    income = [IncomeItem(kind="salary", amount=1_200_000, withholding=1_50_000)]
    ret = compute(TaxpayerProfile(regime_preference="new"), income)
    extractions = [ExtractionResult(
        doc_id="26as", doc_type=DocType.FORM26AS,
        fields=[ExtractedField(name="tds", value=90_000, confidence=0.95, source_doc="26as")],
    )]
    audit = score_return(ret, income, [], extractions)
    assert any(f.code == "tds_exceeds_26as" for f in audit.flags)
    assert audit.band in ("medium", "high")


def test_deductions_at_cap_flagged():
    income = [IncomeItem(kind="salary", amount=2_000_000)]
    deductions = [_ded("80C", 150_000), _ded("SEC24B", 200_000, kind=DeductionKind.HOUSE_PROPERTY)]
    ret = compute(TaxpayerProfile(regime_preference="old"), income, deductions)
    audit = score_return(ret, income, deductions, [])
    assert any(f.code == "deductions_at_cap" for f in audit.flags)


def test_needs_review_deduction_flagged():
    income = [IncomeItem(kind="salary", amount=1_200_000)]
    hra = _ded("HRA", 200_000, kind=DeductionKind.SALARY_EXEMPTION, needs_review=True)
    ret = compute(TaxpayerProfile(regime_preference="old"), income, [hra])
    audit = score_return(ret, income, [hra], [])
    assert any(f.code == "deduction_needs_confirmation" for f in audit.flags)


def test_low_confidence_extraction_flagged():
    income = [IncomeItem(kind="salary", amount=1_200_000)]
    ret = compute(TaxpayerProfile(regime_preference="new"), income)
    extractions = [ExtractionResult(
        doc_id="f16", doc_type=DocType.FORM16,
        fields=[ExtractedField(name="gross_salary", value=1_200_000, confidence=0.4,
                               source_doc="f16")],
    )]
    audit = score_return(ret, income, [], extractions)
    assert any(f.code == "low_confidence_extraction" for f in audit.flags)
