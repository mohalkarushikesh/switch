"""Typed data models shared across the agent pipeline."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    """Lifecycle states an invoice moves through as agents act on it."""

    RECEIVED = "received"        # ingested, not yet scored
    SCORED = "scored"            # risk assessment attached
    APPROVED = "approved"        # cleared for automatic payment
    NEEDS_REVIEW = "needs_review"  # routed to a human approver
    REJECTED = "rejected"        # blocked (too risky)
    PAID = "paid"                # payment released successfully
    FAILED = "failed"            # payment attempted but could not complete


class Invoice(BaseModel):
    """A payable invoice as it enters the system."""

    invoice_id: str
    vendor_name: str
    vendor_account: str          # destination account for payment
    amount: float
    currency: str = "USD"
    issue_date: date
    due_date: date
    line_items: list[str] = Field(default_factory=list)
    memo: str | None = None


class RiskAssessment(BaseModel):
    """Output of the risk/fraud scoring agent."""

    risk_score: int              # 0 (safe) .. 100 (almost certainly fraud)
    fraud_flags: list[str]       # short reasons the score was raised
    rationale: str               # human-readable explanation
    source: str                  # "llm" or "heuristic" — which path produced this


class ApprovalDecision(BaseModel):
    """Output of the approval-routing agent."""

    status: InvoiceStatus        # APPROVED, NEEDS_REVIEW, or REJECTED
    reason: str
    requires_human: bool


class PaymentResult(BaseModel):
    """Output of the auto-pay agent."""

    paid: bool
    transaction_id: str | None
    reason: str


class PolicyViolation(BaseModel):
    """A rule the policy-governance layer flagged on an invoice."""

    code: str          # machine-readable rule id, e.g. "exceeds_absolute_ceiling"
    severity: str      # "block" (force reject) or "flag" (force human review)
    message: str       # human-readable explanation


class ProcessedInvoice(BaseModel):
    """The full record of everything that happened to one invoice.

    This is the auditable artifact — it carries each agent's output plus a
    step-by-step trail so any decision can be reconstructed after the fact.
    """

    invoice: Invoice
    status: InvoiceStatus
    assessment: RiskAssessment | None = None
    decision: ApprovalDecision | None = None
    payment: PaymentResult | None = None
    redacted_pii: list[str] = Field(default_factory=list)      # PII entity types the data layer scrubbed
    policy_violations: list[PolicyViolation] = Field(default_factory=list)
    audit_trail: list[str] = Field(default_factory=list)
