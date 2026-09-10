"""The rule catalog - the single source of truth for citations.

Both sides of the system point at this map: the deterministic engine stamps each
`TaxLine` with the rule it applied, and the grounding guardrail rejects any
deduction the researcher cites that is not in here. Because it is one map, a
citation on a report and a citation on an engine line can never disagree about
what "Section 80C" means. The corpus markdown under data/corpus carries the same
rule_ids; `tax-ingest` warns if the two drift apart.
"""

from __future__ import annotations

from taxpilot.models import Citation

_ACT = "Income-tax Act, 1961"

RULES: dict[str, Citation] = {
    "SALARY-INCOME": Citation(
        rule_id="SALARY-INCOME", source=_ACT, section="Section 15-17 (Salary)"
    ),
    "SALARY-STD-DED": Citation(
        rule_id="SALARY-STD-DED", source=_ACT, section="Section 16(ia) Standard Deduction"
    ),
    "INTEREST-INCOME": Citation(
        rule_id="INTEREST-INCOME", source=_ACT, section="Section 56 (Income from Other Sources)"
    ),
    "SEC24B": Citation(
        rule_id="SEC24B", source=_ACT, section="Section 24(b) Home-Loan Interest"
    ),
    "HRA": Citation(rule_id="HRA", source=_ACT, section="Section 10(13A) House Rent Allowance"),
    "80C": Citation(rule_id="80C", source=_ACT, section="Section 80C"),
    "80CCD1B": Citation(rule_id="80CCD1B", source=_ACT, section="Section 80CCD(1B) NPS"),
    "80D": Citation(rule_id="80D", source=_ACT, section="Section 80D Health Insurance"),
    "80TTA": Citation(rule_id="80TTA", source=_ACT, section="Section 80TTA Savings Interest"),
    "80TTB": Citation(rule_id="80TTB", source=_ACT, section="Section 80TTB (Senior) Interest"),
    "80G": Citation(rule_id="80G", source=_ACT, section="Section 80G Donations"),
    "SLAB-NEW-2024": Citation(
        rule_id="SLAB-NEW-2024", source="Finance (No. 2) Act, 2024",
        section="Section 115BAC New-Regime Slabs (FY 2024-25)",
    ),
    "SLAB-OLD-2024": Citation(
        rule_id="SLAB-OLD-2024", source="Finance (No. 2) Act, 2024",
        section="Old-Regime Slabs (FY 2024-25)",
    ),
    "REBATE-87A": Citation(rule_id="REBATE-87A", source=_ACT, section="Section 87A Rebate"),
    "SURCHARGE": Citation(rule_id="SURCHARGE", source=_ACT, section="Surcharge on Income Tax"),
    "CESS": Citation(
        rule_id="CESS", source="Finance (No. 2) Act, 2024", section="Health & Education Cess (4%)"
    ),
    "TDS": Citation(rule_id="TDS", source=_ACT, section="Section 192/194 Tax Deducted at Source"),
}


def cite(rule_id: str) -> Citation:
    """Look up a citation, or raise if the engine references an unknown rule."""
    return RULES[rule_id]


def is_known(rule_id: str) -> bool:
    return rule_id in RULES
