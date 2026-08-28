"""Orchestrator: chains the agents and wraps them in governance layers.

    Invoice
      -> [Data]     redact PII before it reaches the LLM
      -> [Risk]     score fraud/risk (LLM on redacted view, else heuristic)
      -> [Approval] route: auto-pay / review / reject
      -> [Policy]   enforce hard rules (can override the approval decision)
      -> [Payment]  release funds for approved invoices
      -> [Audit]    persist the full record
    -> ProcessedInvoice

Every step appends to the invoice's audit trail, which is the core governance
promise: after the fact, you can see exactly what happened and why.
"""

from __future__ import annotations

from .agents import ApprovalAgent, IngestAgent, PaymentAgent, RiskAgent
from .config import settings
from .governance import AuditLog, PIIRedactor, PolicyEngine
from .ledger import Ledger
from .models import ApprovalDecision, Invoice, InvoiceStatus, ProcessedInvoice
from .notify import Notification, Notifier


class Custodian:
    def __init__(
        self,
        ledger: Ledger | None = None,
        redactor: PIIRedactor | None = None,
        policy: PolicyEngine | None = None,
        audit_log: AuditLog | None = None,
        notifier: Notifier | None = None,
    ):
        # A single ledger is shared across all payments in this run.
        self.ledger = ledger or Ledger(balance=settings.ledger_balance)
        self.ingest = IngestAgent()
        self.risk = RiskAgent()
        self.approval = ApprovalAgent()
        self.payment = PaymentAgent(self.ledger)

        # Governance layers (data + policy always on; audit log optional).
        self.redactor = redactor or PIIRedactor()
        self.policy = policy or PolicyEngine()
        self.audit_log = audit_log

        # Notifications (optional): fire on rejected / high-risk invoices.
        self.notifier = notifier
        self.notify_min_risk = settings.notify_min_risk

    def process(self, invoice: Invoice, is_duplicate: bool = False) -> ProcessedInvoice:
        """Run one invoice through the full pipeline and return its record.

        is_duplicate is passed to the policy layer, which blocks re-submissions.
        """
        record = ProcessedInvoice(invoice=invoice, status=InvoiceStatus.RECEIVED)
        record.audit_trail.append(
            f"Ingested invoice {invoice.invoice_id} from '{invoice.vendor_name}' "
            f"for {invoice.amount} {invoice.currency}."
        )

        # 0. Data governance — scrub PII before anything leaves for the LLM.
        redacted_invoice, pii = self.redactor.redact_invoice(invoice)
        record.redacted_pii = pii
        if pii:
            record.audit_trail.append(f"Data layer: redacted PII types {pii} before LLM.")

        # 1. Risk / fraud scoring (LLM sees the redacted view).
        assessment = self.risk.assess(invoice, llm_invoice=redacted_invoice)
        record.assessment = assessment
        record.status = InvoiceStatus.SCORED
        record.audit_trail.append(
            f"Risk scored {assessment.risk_score}/100 via {assessment.source}. "
            f"Flags: {assessment.fraud_flags or 'none'}."
        )

        # 2. Approval routing (risk-based).
        decision = self.approval.decide(invoice, assessment)
        record.audit_trail.append(
            f"Approval decision: {decision.status.value} — {decision.reason}"
        )

        # 3. Policy governance — deterministic rules that can override approval.
        violations = self.policy.evaluate(invoice, is_duplicate=is_duplicate)
        record.policy_violations = violations
        for v in violations:
            record.audit_trail.append(f"Policy [{v.severity}] {v.code}: {v.message}")

        blocks = [v for v in violations if v.severity == "block"]
        flags = [v for v in violations if v.severity == "flag"]
        if blocks:
            decision = ApprovalDecision(
                status=InvoiceStatus.REJECTED,
                reason=f"Blocked by policy: {', '.join(v.code for v in blocks)}.",
                requires_human=False,
            )
            record.audit_trail.append(
                f"Policy override → rejected ({len(blocks)} blocking violation(s))."
            )
        elif flags and decision.status is InvoiceStatus.APPROVED:
            decision = ApprovalDecision(
                status=InvoiceStatus.NEEDS_REVIEW,
                reason=f"Flagged by policy: {', '.join(v.code for v in flags)}.",
                requires_human=True,
            )
            record.audit_trail.append("Policy override → routed to human review.")

        record.decision = decision
        record.status = decision.status

        # 4. Payment (only executes for APPROVED invoices).
        payment = self.payment.pay(invoice, decision)
        record.payment = payment
        if payment.paid:
            record.status = InvoiceStatus.PAID
            record.audit_trail.append(
                f"Payment released: {payment.transaction_id} — {payment.reason}"
            )
        elif decision.status is InvoiceStatus.APPROVED:
            # Approved but payment failed (e.g. insufficient funds).
            record.status = InvoiceStatus.FAILED
            record.audit_trail.append(f"Payment failed: {payment.reason}")
        else:
            record.audit_trail.append(f"No payment: {payment.reason}")

        # 5. Notifications — alert on invoices that need human attention.
        self._maybe_notify(record)

        # 6. Audit governance — persist the full record if a log is configured.
        if self.audit_log is not None:
            self.audit_log.record(record)

        return record

    def _maybe_notify(self, record: ProcessedInvoice) -> None:
        """Send a notification if the invoice was rejected or scored high-risk."""
        if self.notifier is None:
            return
        risk = record.assessment.risk_score if record.assessment else 0
        events: list[str] = []
        if record.status is InvoiceStatus.REJECTED:
            events.append("rejected")
        if risk >= self.notify_min_risk:
            events.append("high_risk")
        if not events:
            return

        inv = record.invoice
        self.notifier.send(Notification(
            invoice_id=inv.invoice_id,
            events=events,
            status=record.status.value,
            risk_score=risk,
            vendor_name=inv.vendor_name,
            amount=inv.amount,
            message=(
                f"Invoice {inv.invoice_id} from '{inv.vendor_name}' "
                f"({inv.amount} {inv.currency}) — {', '.join(events)} "
                f"[status={record.status.value}, risk={risk}]."
            ),
        ))
        record.audit_trail.append(f"Notification sent ({', '.join(events)}).")

    def process_many(self, invoices: list[Invoice]) -> list[ProcessedInvoice]:
        """Process a batch of invoices in order, flagging in-batch duplicates."""
        seen: set[str] = set()
        records: list[ProcessedInvoice] = []
        for inv in invoices:
            records.append(self.process(inv, is_duplicate=inv.invoice_id in seen))
            seen.add(inv.invoice_id)
        return records
