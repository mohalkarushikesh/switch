"""Rupee formatting with the Indian digit grouping (lakh/crore).

Indian numbering groups the last three digits, then in pairs: 1,23,45,678 - not
the western 12,345,678. One helper, used by the report, the CLI and the guardrail
that parses figures back out of a narrative, so the grouping is identical
everywhere and the figure-integrity check can round-trip it.
"""

from __future__ import annotations


def group_inr(n: int) -> str:
    """Group an integer with Indian commas: 1355000 -> '13,55,000'."""
    sign = "-" if n < 0 else ""
    digits = str(abs(int(n)))
    if len(digits) <= 3:
        return sign + digits
    head, tail = digits[:-3], digits[-3:]
    # Insert a comma every two digits from the right of the head.
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    parts.insert(0, head)
    return sign + ",".join(parts) + "," + tail


def rupees(n: int) -> str:
    """A rupee amount for display: ₹13,55,000."""
    return "₹" + group_inr(n)
