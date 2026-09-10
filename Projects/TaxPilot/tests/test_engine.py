"""The engine is the part that must be exactly right, so it is tested against
hand-computed FY 2024-25 figures rather than against itself."""

import pytest

from taxpilot.calc import brackets as B
from taxpilot.calc.engine import (
    UnsupportedTaxYearError,
    compute,
    slab_tax,
    whole_rupee,
)
from taxpilot.models import (
    AgeCategory,
    Citation,
    DeductionCandidate,
    DeductionKind,
    IncomeItem,
    Regime,
    TaxpayerProfile,
)


def _profile(age=AgeCategory.BELOW_60, regime="auto"):
    return TaxpayerProfile(age_category=age, regime_preference=regime)


def _ded(rule_id, amount, kind=DeductionKind.CHAPTER_VIA):
    return DeductionCandidate(name=rule_id, kind=kind, amount=amount,
                              citation=Citation(rule_id=rule_id), grounded=True)


def test_whole_rupee_rounds_half_up():
    assert whole_rupee(2749.5) == 2750
    assert whole_rupee(2.4) == 2


def test_slab_tax_new_regime_known_points():
    # Full new-regime schedule at 15,00,000: 20k + 30k + 30k + 60k.
    assert slab_tax(1_500_000, B.NEW_REGIME_SLABS_2024) == 140_000


def test_slab_tax_old_regime_below_60():
    assert slab_tax(1_000_000, B.OLD_REGIME_SLABS_2024[AgeCategory.BELOW_60]) == 112_500


def test_new_regime_salary_only():
    ret = compute(_profile(regime="new"),
                  [IncomeItem(kind="salary", amount=1_200_000)])
    assert ret.regime == Regime.NEW
    assert ret.total_income == 1_125_000            # 12,00,000 - 75,000 std deduction
    assert ret.tax_before_rebate == 68_750
    assert ret.cess == 2_750
    assert ret.total_tax == 71_500


def test_87a_rebate_new_regime_makes_7l_tax_free():
    # Salary 7,75,000 - 75,000 std = 7,00,000 total income -> full rebate -> nil tax.
    ret = compute(_profile(regime="new"), [IncomeItem(kind="salary", amount=775_000)])
    assert ret.total_income == 700_000
    assert ret.rebate_87a == 20_000
    assert ret.total_tax == 0


def test_87a_rebate_old_regime_at_5l():
    ret = compute(_profile(regime="old"), [IncomeItem(kind="salary", amount=550_000)])
    assert ret.total_income == 500_000
    assert ret.total_tax == 0


def test_senior_citizen_higher_exemption():
    ret = compute(_profile(age=AgeCategory.SENIOR, regime="old"),
                  [IncomeItem(kind="salary", amount=350_000)])
    assert ret.total_income == 300_000              # 3,50,000 - 50,000 std
    assert ret.total_tax == 0                       # within the senior 3L exemption


def test_auto_regime_picks_the_cheaper_and_shows_the_other():
    income = [
        IncomeItem(kind="salary", amount=1_400_000, withholding=1_20_000),
        IncomeItem(kind="interest", amount=30_000),
    ]
    deductions = [
        _ded("80C", 150_000),
        _ded("80D", 25_000),
        _ded("SEC24B", 200_000, kind=DeductionKind.HOUSE_PROPERTY),
    ]
    ret = compute(_profile(), income, deductions)
    assert ret.regime == Regime.NEW                 # new (1,15,440) beats old (1,18,560)
    assert ret.total_income == 1_355_000            # new: 14,00,000 - 75,000 + 30,000
    assert ret.total_tax == 1_15_440
    assert ret.alternative_regime_tax == 1_18_560
    assert ret.refund_or_due == 4_560               # TDS 1,20,000 - tax 1,15,440


def test_forcing_old_regime_applies_deductions():
    income = [
        IncomeItem(kind="salary", amount=1_400_000, withholding=1_20_000),
        IncomeItem(kind="interest", amount=30_000),
    ]
    deductions = [
        _ded("80C", 150_000),
        _ded("80D", 25_000),
        _ded("SEC24B", 200_000, kind=DeductionKind.HOUSE_PROPERTY),
    ]
    ret = compute(_profile(regime="old"), income, deductions)
    assert ret.regime == Regime.OLD
    assert ret.deductions_total == 175_000          # 80C + 80D (capped), old regime only
    assert ret.total_income == 1_005_000            # GTI 11,80,000 - 1,75,000
    assert ret.total_tax == 1_18_560


def test_80c_is_capped_at_150000():
    ret = compute(_profile(regime="old"),
                  [IncomeItem(kind="salary", amount=2_000_000)], [_ded("80C", 250_000)])
    assert ret.deductions_total == 150_000          # claim of 2,50,000 capped to 1,50,000


def test_new_regime_ignores_chapter_via():
    ret = compute(_profile(regime="new"),
                  [IncomeItem(kind="salary", amount=2_000_000)], [_ded("80C", 150_000)])
    assert ret.deductions_total == 0                # no Chapter VI-A under the new regime


def test_every_line_cites_a_known_rule_or_nothing():
    from taxpilot.knowledge.rules import is_known

    ret = compute(_profile(regime="old"),
                  [IncomeItem(kind="salary", amount=1_400_000, withholding=100_000)],
                  [_ded("80C", 150_000)])
    for line in ret.lines:
        if line.citation is not None:
            assert is_known(line.citation.rule_id), line.line


def test_unsupported_year_is_a_loud_error():
    with pytest.raises(UnsupportedTaxYearError):
        compute(_profile(), [IncomeItem(kind="salary", amount=1)], tax_year=1999)
