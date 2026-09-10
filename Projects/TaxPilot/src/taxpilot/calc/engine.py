"""The deterministic tax engine - the part the LLM never touches.

Given a taxpayer profile, normalized income and a set of grounded deductions, this
computes the return under BOTH the old and new regimes, keeps the one with the
lower tax (unless the taxpayer forced a regime), and stamps every figure with the
rule it applied. There is no model call anywhere in this module, and the same
inputs always produce the same return - which is what makes a figure defensible in
front of the assessing officer.

Scope note: this implements the common resident-individual path - salary (with the
Section 16(ia) standard deduction), interest and other income, self-occupied
home-loan interest under Section 24(b), the Chapter VI-A deductions (80C,
80CCD(1B), 80D, 80TTA/80TTB, 80G), the Section 87A rebate, surcharge with marginal
relief, and the 4% Health & Education Cess, reconciled against TDS. It does not
model capital gains, business income, HRA computation (a rent receipt is sent to
review instead), or the Section 288A/288B round-to-ten. Those are out of scope,
not silently wrong: an input that needs one is a reviewer-gate candidate.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from taxpilot.calc import brackets as B
from taxpilot.knowledge.rules import cite
from taxpilot.models import (
    AgeCategory,
    DeductionCandidate,
    DeductionKind,
    IncomeItem,
    Regime,
    TaxLine,
    TaxpayerProfile,
    TaxReturn,
)


def whole_rupee(value: float) -> int:
    """Round to a whole rupee, half up (returns are rounded to the rupee)."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class UnsupportedTaxYearError(ValueError):
    def __init__(self, year: int) -> None:
        super().__init__(
            f"tax year {year} is not supported; the engine ships constants for "
            f"{B.SUPPORTED_YEARS} (FY start year)"
        )


# ------------------------------------------------------------------ primitives


def slab_tax(income: int, slabs: list[tuple[int, float]]) -> int:
    """Progressive tax over a slab schedule."""
    if income <= 0:
        return 0
    tax = 0.0
    for index, (lower, rate) in enumerate(slabs):
        if income <= lower:
            break
        upper = slabs[index + 1][0] if index + 1 < len(slabs) else float("inf")
        tax += (min(income, upper) - lower) * rate
    return whole_rupee(tax)


def _slabs_for(regime: Regime, age: AgeCategory) -> list[tuple[int, float]]:
    if regime == Regime.NEW:
        return B.NEW_REGIME_SLABS_2024
    return B.OLD_REGIME_SLABS_2024[age]


def _standard_deduction(regime: Regime, has_salary: bool) -> int:
    if not has_salary:
        return 0
    return B.STANDARD_DEDUCTION_NEW_2024 if regime == Regime.NEW else B.STANDARD_DEDUCTION_OLD_2024


def _rebate_87a(regime: Regime, total_income: int, tax: int) -> int:
    """Section 87A rebate, with the new regime's marginal relief above 7 lakh."""
    if regime == Regime.NEW:
        if total_income <= B.REBATE_87A_NEW_THRESHOLD:
            return min(tax, B.REBATE_87A_NEW_CAP)
        # Marginal relief: tax cannot exceed income over the threshold.
        return max(0, tax - (total_income - B.REBATE_87A_NEW_THRESHOLD))
    if total_income <= B.REBATE_87A_OLD_THRESHOLD:
        return min(tax, B.REBATE_87A_OLD_CAP)
    return 0


def _surcharge_rate(income: int, regime: Regime) -> float:
    """The surcharge rate applicable at a given total income."""
    rate = 0.0
    for threshold, band_rate in B.SURCHARGE_BANDS:
        if income > threshold:
            rate = band_rate
    return min(rate, B.SURCHARGE_NEW_MAX) if regime == Regime.NEW else rate


def _surcharge(tax: int, total_income: int, regime: Regime, age: AgeCategory) -> int:
    """Surcharge on income tax above 50 lakh, with marginal relief."""
    rate = 0.0
    threshold = 0
    for band_threshold, band_rate in B.SURCHARGE_BANDS:
        if total_income > band_threshold:
            rate, threshold = band_rate, band_threshold
    if rate == 0.0:
        return 0
    if regime == Regime.NEW:
        rate = min(rate, B.SURCHARGE_NEW_MAX)

    raw = tax * rate
    # Marginal relief: income-tax + surcharge must not exceed (tax + surcharge) at
    # the band threshold plus the income earned above it. The surcharge already
    # leviable at the threshold (the previous band's rate) is part of that
    # ceiling - omitting it makes relief far too generous above 1cr/2cr/5cr.
    slabs = _slabs_for(regime, age)
    tax_at_threshold = slab_tax(threshold, slabs)
    surcharge_at_threshold = tax_at_threshold * _surcharge_rate(threshold, regime)
    allowed = tax_at_threshold + surcharge_at_threshold + (total_income - threshold)
    if tax + raw > allowed:
        return max(0, whole_rupee(allowed - tax))
    return whole_rupee(raw)


def _chapter_via(
    deductions: list[DeductionCandidate], gti: int, profile: TaxpayerProfile
) -> tuple[int, dict[str, int]]:
    """Chapter VI-A total (old regime), with the statutory caps. Returns (total, applied)."""
    by_rule: dict[str, int] = {}
    for c in deductions:
        if c.kind == DeductionKind.CHAPTER_VIA:
            by_rule[c.citation.rule_id] = by_rule.get(c.citation.rule_id, 0) + c.amount

    senior = profile.age_category in (AgeCategory.SENIOR, AgeCategory.SUPER_SENIOR)
    applied: dict[str, int] = {}
    if "80C" in by_rule:
        applied["80C"] = min(by_rule["80C"], B.CAP_80C)
    if "80CCD1B" in by_rule:
        applied["80CCD1B"] = min(by_rule["80CCD1B"], B.CAP_80CCD1B)
    if "80D" in by_rule:
        applied["80D"] = min(by_rule["80D"], B.CAP_80D_SENIOR if senior else B.CAP_80D_BELOW_60)
    tt = by_rule.get("80TTA", 0) + by_rule.get("80TTB", 0)
    if tt:
        applied["80TTB" if senior else "80TTA"] = min(tt, B.CAP_80TTB if senior else B.CAP_80TTA)
    if "80G" in by_rule:
        applied["80G"] = by_rule["80G"]  # face value (qualifying-limit split simplified)
    for rule_id, amount in by_rule.items():
        if rule_id not in ("80C", "80CCD1B", "80D", "80TTA", "80TTB", "80G"):
            applied[rule_id] = amount

    total = min(sum(applied.values()), max(0, gti))
    return total, applied


def _house_property_loss(deductions: list[DeductionCandidate]) -> int:
    total = sum(c.amount for c in deductions if c.kind == DeductionKind.HOUSE_PROPERTY)
    return min(total, B.CAP_SEC24B)


class _RegimeResult:
    def __init__(self, **kw: object) -> None:
        self.__dict__.update(kw)


def _compute_regime(
    regime: Regime,
    profile: TaxpayerProfile,
    gross_salary: int,
    interest: int,
    other: int,
    deductions: list[DeductionCandidate],
) -> _RegimeResult:
    std = _standard_deduction(regime, gross_salary > 0)
    salary_income = max(0, gross_salary - std)

    # Self-occupied home-loan interest is a house-property set-off allowed only
    # under the old regime; the new regime forgoes it.
    hp_loss = _house_property_loss(deductions) if regime == Regime.OLD else 0
    gti = salary_income + interest + other - hp_loss

    if regime == Regime.OLD:
        chapter_via, applied = _chapter_via(deductions, gti, profile)
    else:
        chapter_via, applied = 0, {}

    total_income = max(0, gti - chapter_via)
    slabs = _slabs_for(regime, profile.age_category)
    tax_before_rebate = slab_tax(total_income, slabs)
    rebate = _rebate_87a(regime, total_income, tax_before_rebate)
    tax_after_rebate = max(0, tax_before_rebate - rebate)
    surcharge = _surcharge(tax_after_rebate, total_income, regime, profile.age_category)
    cess = whole_rupee((tax_after_rebate + surcharge) * B.CESS_RATE)
    total_tax = tax_after_rebate + surcharge + cess

    return _RegimeResult(
        regime=regime, std=std, salary_income=salary_income, hp_loss=hp_loss, gti=gti,
        chapter_via=chapter_via, applied=applied, total_income=total_income,
        tax_before_rebate=tax_before_rebate, rebate=rebate, surcharge=surcharge, cess=cess,
        total_tax=total_tax,
    )


# --------------------------------------------------------------------- compute


def compute(
    profile: TaxpayerProfile,
    income: list[IncomeItem],
    deductions: list[DeductionCandidate] | None = None,
    *,
    tax_year: int = 2024,
) -> TaxReturn:
    """Compute the return, choosing the cheaper regime. The engine's only entry point."""
    if tax_year not in B.SUPPORTED_YEARS:
        raise UnsupportedTaxYearError(tax_year)
    deductions = deductions or []

    gross_salary = sum(i.amount for i in income if i.kind == "salary")
    interest = sum(i.amount for i in income if i.kind == "interest")
    other = sum(i.amount for i in income if i.kind == "other")
    tds = sum(i.withholding for i in income)

    old = _compute_regime(Regime.OLD, profile, gross_salary, interest, other, deductions)
    new = _compute_regime(Regime.NEW, profile, gross_salary, interest, other, deductions)

    if profile.regime_preference == "old":
        chosen, alternative = old, new
    elif profile.regime_preference == "new":
        chosen, alternative = new, old
    else:
        # Auto: lower tax wins; ties go to the new regime (the statutory default).
        chosen, alternative = (new, old) if new.total_tax <= old.total_tax else (old, new)

    return _build_return(chosen, alternative, gross_salary, interest, other, tds, tax_year)


def _build_return(
    r: _RegimeResult, alt: _RegimeResult,
    gross_salary: int, interest: int, other: int, tds: int, tax_year: int,
) -> TaxReturn:
    lines: list[TaxLine] = []

    def add(line: str, label: str, amount: int, rule_id: str | None = None) -> None:
        lines.append(TaxLine(line=line, label=label, amount=amount,
                             citation=cite(rule_id) if rule_id else None))

    if gross_salary:
        add("gross_salary", "Gross salary", gross_salary, "SALARY-INCOME")
        add("standard_deduction", "Standard deduction (Sec 16(ia))", r.std, "SALARY-STD-DED")
    if interest:
        add("interest", "Interest income", interest, "INTEREST-INCOME")
    if other:
        add("other", "Other income", other, "INTEREST-INCOME")
    if r.hp_loss:
        add("house_property", "Home-loan interest set-off (Sec 24(b))", r.hp_loss, "SEC24B")
    add("gross_total_income", "Gross total income", r.gti)

    _SECTION_RULE = {
        "80C": "80C", "80CCD1B": "80CCD1B", "80D": "80D",
        "80TTA": "80TTA", "80TTB": "80TTB", "80G": "80G",
    }
    for rule_id, amount in r.applied.items():
        add(f"ded_{rule_id.lower()}", f"Deduction {rule_id}", amount,
            _SECTION_RULE.get(rule_id, rule_id))
    if r.chapter_via:
        add("chapter_via", "Total Chapter VI-A deductions", r.chapter_via)
    add("total_income", "Total (taxable) income", r.total_income)

    slab_rule = "SLAB-NEW-2024" if r.regime == Regime.NEW else "SLAB-OLD-2024"
    add("tax_before_rebate", "Tax on total income", r.tax_before_rebate, slab_rule)
    if r.rebate:
        add("rebate_87a", "Rebate under Section 87A", r.rebate, "REBATE-87A")
    if r.surcharge:
        add("surcharge", "Surcharge", r.surcharge, "SURCHARGE")
    add("cess", "Health & Education Cess (4%)", r.cess, "CESS")
    add("total_tax", "Total tax liability", r.total_tax)
    add("tds", "Tax deducted at source (TDS)", tds, "TDS")

    refund_or_due = tds - r.total_tax
    add("refund_or_due", "Refund" if refund_or_due >= 0 else "Balance payable", abs(refund_or_due))
    add("alternative_regime_tax",
        f"Tax under the {alt.regime.value} regime (not chosen)", alt.total_tax)

    return TaxReturn(
        tax_year=tax_year,
        regime=r.regime,
        gross_total_income=r.gti,
        deductions_total=r.chapter_via,
        total_income=r.total_income,
        tax_before_rebate=r.tax_before_rebate,
        rebate_87a=r.rebate,
        surcharge=r.surcharge,
        cess=r.cess,
        total_tax=r.total_tax,
        tds=tds,
        refund_or_due=refund_or_due,
        alternative_regime_tax=alt.total_tax,
        lines=lines,
    )
