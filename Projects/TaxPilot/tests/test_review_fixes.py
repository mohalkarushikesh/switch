"""Regression tests for the bugs the adversarial review confirmed and I fixed.

Each test names the defect it guards against so a future change that reintroduces
it fails loudly.
"""

from taxpilot.calc import compute
from taxpilot.config import Settings
from taxpilot.extraction.extractor import _coerce
from taxpilot.guardrails import patterns
from taxpilot.guardrails.pipeline import Guardrails
from taxpilot.models import AgeCategory, IncomeItem, Regime, TaxpayerProfile

# ---- engine: surcharge marginal relief includes threshold surcharge ----

def test_surcharge_marginal_relief_above_one_crore():
    # Old regime, below 60, no deductions, gross salary 1,00,60,000 -> total income
    # 1,00,10,000 (just over 1 crore, 15% band). Correct surcharge Rs 2,88,250.
    ret = compute(
        TaxpayerProfile(age_category=AgeCategory.BELOW_60, regime_preference="old"),
        [IncomeItem(kind="salary", amount=1_00_60_000)],
    )
    assert ret.regime == Regime.OLD
    assert ret.surcharge == 2_88_250          # not the buggy 7,000
    assert ret.total_tax == 32_27_900


# ---- extraction: the Indian rupee suffix "/-" must not zero an amount ----

def test_rupee_suffix_slash_dash_is_read_as_a_number():
    assert _coerce("Rs. 1,50,000/-") == 1_50_000.0
    assert _coerce("1,50,000/-") == 1_50_000.0


def test_separated_identifier_or_date_stays_a_string():
    assert _coerce("15/04/2024") == "15/04/2024"   # a date, not 15
    assert _coerce("412-55-8830") == "412-55-8830"


# ---- guardrails: figure_integrity cannot be bypassed ----

def test_rupee_amounts_catches_bare_grouped_and_worded():
    assert 12_00_000 in patterns.rupee_amounts("total income is 12,00,000")
    assert 5_00_000 in patterns.rupee_amounts("your refund is ₹5 lakh")
    assert 1_50_00_000 in patterns.rupee_amounts("a gain of 1.5 crore")


def test_rupee_amounts_does_not_match_a_year_after_rs_word():
    # "years 2024" must not be read as "rs 2024" (word boundary on \brs).
    assert 2024 not in patterns.rupee_amounts("over the years 2024 and 2025 slabs changed")


def test_figure_integrity_blocks_a_bare_invented_number():
    ret = compute(TaxpayerProfile(regime_preference="new"),
                  [IncomeItem(kind="salary", amount=12_00_000)])
    guardrails = Guardrails(settings=Settings(enable_guardrails=True))
    # Bare Indian-grouped figure the engine never computed, no ₹ prefix.
    result = guardrails.check_output("A hidden refund of 9,99,999 applies.", ret, [],
                                     use_llm=False)
    assert result.blocked
    assert any(o.layer == "figure_integrity" and o.action == "block" for o in result.outcomes)


# ---- guardrails: PII redaction ----

def test_hyphenated_aadhaar_is_masked():
    text, hits = patterns.redact_pii("Aadhaar 1234-5678-9012 on file")
    assert "aadhaar" in hits
    assert "1234-5678-9012" not in text
    assert "XXXX XXXX 9012" in text


def test_twelve_digit_account_is_fully_redacted_not_partially_masked():
    text, hits = patterns.redact_pii("Refund credited to A/c 123456789012")
    assert "bank_account" in hits
    assert "[REDACTED:account]" in text
    assert "9012" not in text          # not partially masked as an Aadhaar
