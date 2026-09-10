"""Guardrails: deterministic detectors plus LLM review, inbound and outbound.

The headline layer is figure_integrity - it enforces that no dollar figure the
engine did not compute reaches the report."""

from taxpilot.guardrails.pipeline import GuardrailResult, Guardrails, get_guardrails

__all__ = ["Guardrails", "GuardrailResult", "get_guardrails"]
