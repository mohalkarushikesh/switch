"""Tax-year constants for the deterministic engine.

Everything here is a published figure for FY 2024-25 (AY 2025-26) for a resident
individual, from the Finance (No. 2) Act, 2024 and the Income-tax Act, 1961. They
live in one module so the engine reads as arithmetic over named constants.

`SUPPORTED_YEARS` uses the financial-year start (2024 == FY 2024-25); the engine
refuses a year it has no constants for rather than applying the wrong ones.
"""

from __future__ import annotations

from taxpilot.models import AgeCategory

SUPPORTED_YEARS = (2024,)

# ---------------------------------------------------------------- slabs

#: (lower_bound, rate). Each rate applies from its bound up to the next.
#: New regime (Section 115BAC), FY 2024-25 - the same slabs for every age.
NEW_REGIME_SLABS_2024: list[tuple[int, float]] = [
    (0, 0.00), (300_000, 0.05), (700_000, 0.10),
    (1_000_000, 0.15), (1_200_000, 0.20), (1_500_000, 0.30),
]

#: Old regime - the basic exemption limit rises with age.
OLD_REGIME_SLABS_2024: dict[AgeCategory, list[tuple[int, float]]] = {
    AgeCategory.BELOW_60: [(0, 0.00), (250_000, 0.05), (500_000, 0.20), (1_000_000, 0.30)],
    AgeCategory.SENIOR: [(0, 0.00), (300_000, 0.05), (500_000, 0.20), (1_000_000, 0.30)],
    AgeCategory.SUPER_SENIOR: [(0, 0.00), (500_000, 0.20), (1_000_000, 0.30)],
}

# ---------------------------------------------------------- standard deduction

#: Section 16(ia), salaried taxpayers. Higher under the new regime for FY 2024-25.
STANDARD_DEDUCTION_NEW_2024 = 75_000
STANDARD_DEDUCTION_OLD_2024 = 50_000

# --------------------------------------------------------------- 87A rebate

#: Section 87A. Full rebate of the tax up to the cap when total income is within
#: the threshold; the new regime's higher threshold is what makes it "tax-free to
#: 7 lakh".
REBATE_87A_NEW_THRESHOLD = 700_000
REBATE_87A_NEW_CAP = 25_000
REBATE_87A_OLD_THRESHOLD = 500_000
REBATE_87A_OLD_CAP = 12_500

# ------------------------------------------------------------ Chapter VI-A caps

#: Deductions are available under the OLD regime only (the new regime forgoes them
#: in exchange for lower slab rates).
CAP_80C = 150_000               # Section 80C/80CCC/80CCD(1)
CAP_80CCD1B = 50_000            # Section 80CCD(1B) - additional NPS
CAP_80D_BELOW_60 = 25_000       # Section 80D - self, below 60
CAP_80D_SENIOR = 50_000         # Section 80D - self, senior
CAP_80TTA = 10_000              # Section 80TTA - savings interest, below 60
CAP_80TTB = 50_000              # Section 80TTB - interest, senior
CAP_SEC24B = 200_000            # Section 24(b) - self-occupied home-loan interest

# ------------------------------------------------------------------ surcharge

#: (threshold_total_income, rate). Applied to income tax (before cess), with
#: marginal relief. The new regime caps the top surcharge at 25%.
SURCHARGE_BANDS: list[tuple[int, float]] = [
    (5_000_000, 0.10), (10_000_000, 0.15), (20_000_000, 0.25), (50_000_000, 0.37),
]
SURCHARGE_NEW_MAX = 0.25

# ------------------------------------------------------------------ cess

#: Health & Education Cess on (income tax + surcharge).
CESS_RATE = 0.04
