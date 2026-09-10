"""Field extraction (LLM or heuristic) and deterministic normalization."""

from taxpilot.extraction.extractor import Extractor
from taxpilot.extraction.normalize import to_deductions, to_income

__all__ = ["Extractor", "to_income", "to_deductions"]
