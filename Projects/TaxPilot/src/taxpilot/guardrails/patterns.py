"""Deterministic detectors for the cheap guardrail layers.

Regex is the wrong tool for judging whether a document is really a tax document
(the LLM layer does that) but exactly the right tool for finding a PAN or Aadhaar
in an answer, spotting an injection string smuggled into a receipt, or listing the
rupee figures a narrative actually states. These run in microseconds and are the
only layers that ever see raw, unredacted document text.
"""

from __future__ import annotations

import re

#: PII shapes that appear legitimately in Indian tax documents. Not blocked -
#: catalogued, then redacted on the way out so they never reach a shown report or
#: a log. PAN is five letters, four digits, a letter (ABCDE1234F).
PAN_PATTERN = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b")
#: Aadhaar is 12 digits, printed in groups of four separated by a space, hyphen or
#: dot (or run together). Digit look-around keeps it from matching a slice of a
#: longer number (a bank account).
AADHAAR_PATTERN = re.compile(r"(?<!\d)(\d{4})[\s.-]?(\d{4})[\s.-]?(\d{4})(?!\d)")
ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b")

#: Text trying to steer the assistant instead of stating tax facts - the indirect
#: prompt-injection an attacker (or an over-eager client) hides inside a document.
INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above|the|your)\s+"
               r"(?:instructions?|rules?|prompts?)\b", re.I),
    re.compile(r"\bdisregard\s+(?:your|all|the)\s+(?:instructions?|guidelines?|rules?)\b", re.I),
    re.compile(r"\b(?:reveal|show|print|repeat|output)\s+(?:me\s+)?(?:your|the)\s+"
               r"(?:system\s+)?(?:prompt|instructions?)\b", re.I),
    re.compile(r"\balways\s+(?:deduct|claim|add|include|allow)\b", re.I),
    re.compile(r"\b(?:do\s*not|don't|never)\s+report\b", re.I),
    re.compile(r"\b(?:set|make|force)\s+the\s+(?:refund|tax|total|income)\b", re.I),
    re.compile(r"\bmark\s+(?:this|the\s+return)\s+as\s+(?:reviewed|approved|final|filed)\b", re.I),
    re.compile(r"\b(?:the\s+ca|chartered\s+accountant|the\s+preparer)\s+(?:said|approved|wants)\b",
               re.I),
]

#: Rupee amounts in a narrative. Three shapes so the LLM cannot smuggle a figure
#: past figure_integrity: (A) a ₹/Rs-prefixed number with an optional lakh/crore
#: word; (B) a bare number followed by lakh/crore; (C) a bare Indian-grouped
#: number of at least one lakh (e.g. 12,00,000), whose grouping is unmistakably a
#: money amount rather than a year. `\brs` has a word boundary so "years 2024"
#: does not match.
_RUPEE_PREFIXED = re.compile(
    r"(?:₹|\brs\.?)\s?(-?\d[\d,]*(?:\.\d+)?)\s*(lakhs?|crores?)?", re.I)
_WORDED = re.compile(r"\b(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|crores?)\b", re.I)
_INDIAN_GROUPED = re.compile(r"\b\d{1,2}(?:,\d{2})+,\d{3}\b")
_MULTIPLIER = {"lakh": 100_000, "lakhs": 100_000, "crore": 10_000_000, "crores": 10_000_000}


def find_injections(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            hits.append(match.group(0)[:60])
    return hits


def inventory_pii(text: str) -> list[str]:
    """Labels of PII kinds present, without echoing the values."""
    found: list[str] = []
    if PAN_PATTERN.search(text):
        found.append("pan")
    if AADHAAR_PATTERN.search(text):
        found.append("aadhaar")
    if ACCOUNT_PATTERN.search(text):
        found.append("bank_account")
    return found


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Mask PII for display: PAN fully, accounts fully, Aadhaar to its last four.

    Accounts are redacted before Aadhaar so a bare 12-digit account number is
    fully removed rather than partially masked as an Aadhaar (which would leak its
    last four). A separated Aadhaar (with spaces/hyphens) is untouched by the
    account pass and then masked to its last four.
    """
    hits: list[str] = []

    def mask_aadhaar(match: re.Match[str]) -> str:
        return f"XXXX XXXX {match.group(3)}"

    text, n_acct = ACCOUNT_PATTERN.subn("[REDACTED:account]", text)
    if n_acct:
        hits.append("bank_account")
    text, n_aadhaar = AADHAAR_PATTERN.subn(mask_aadhaar, text)
    if n_aadhaar:
        hits.append("aadhaar")
    text, n_pan = PAN_PATTERN.subn("[REDACTED:pan]", text)
    if n_pan:
        hits.append("pan")
    return text, hits


def rupee_amounts(text: str) -> set[int]:
    """Every whole-rupee amount a narrative states, in any of the three shapes."""
    amounts: set[int] = set()

    def add(raw: str, word: str | None) -> None:
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            return
        if word:
            value *= _MULTIPLIER[word.lower()]
        amounts.add(abs(int(round(value))))

    for match in _RUPEE_PREFIXED.finditer(text):
        add(match.group(1), match.group(2))
    for match in _WORDED.finditer(text):
        add(match.group(1), match.group(2))
    for match in _INDIAN_GROUPED.finditer(text):
        add(match.group(0), None)
    return amounts
