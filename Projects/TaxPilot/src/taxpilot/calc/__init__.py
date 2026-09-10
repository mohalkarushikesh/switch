"""The deterministic tax-computation engine. No LLM call lives below this line."""

from taxpilot.calc.engine import compute, whole_rupee

__all__ = ["compute", "whole_rupee"]
