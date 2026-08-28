"""Tests for notifications on rejected / high-risk invoices."""

from __future__ import annotations

from datetime import date

from custodian.ledger import Ledger
from custodian.models import Invoice, InvoiceStatus
from custodian.notify import LogNotifier, Notification, Notifier
from custodian.orchestrator import Custodian


class RecordingNotifier(Notifier):
    """Captures notifications in memory for assertions."""

    def __init__(self) -> None:
        self.sent: list[Notification] = []

    def send(self, note: Notification) -> None:
        self.sent.append(note)


def _invoice(invoice_id="N-1", amount=1234.0, **overrides) -> Invoice:
    base = dict(
        invoice_id=invoice_id,
        vendor_name="Test Vendor",
        vendor_account="TEST-CHK-123456",
        amount=amount,
        issue_date=date(2026, 8, 1),
        due_date=date(2026, 9, 1),
        line_items=["Consulting"],
        memo="Normal invoice.",
    )
    base.update(overrides)
    return Invoice(**base)


def test_clean_low_risk_invoice_sends_no_notification():
    notifier = RecordingNotifier()
    cust = Custodian(Ledger(balance=1_000_000), notifier=notifier)
    cust.process(_invoice("N-CLEAN", 1234.0))  # risk 0, auto-paid
    assert notifier.sent == []


def test_rejected_invoice_notifies():
    notifier = RecordingNotifier()
    cust = Custodian(Ledger(balance=1_000_000), notifier=notifier)
    # Suspicious invoice -> risk 100 -> rejected AND high-risk.
    cust.process(_invoice(
        "N-BAD", 75000.0, vendor_account="X12", line_items=[],
        memo="URGENT wire now immediately",
    ))
    assert len(notifier.sent) == 1
    note = notifier.sent[0]
    assert "rejected" in note.events
    assert "high_risk" in note.events
    assert note.invoice_id == "N-BAD"


def test_mid_risk_below_threshold_sends_no_notification():
    notifier = RecordingNotifier()
    cust = Custodian(Ledger(balance=1_000_000), notifier=notifier)
    # amount 10000 -> large (+25) + round (+15) = risk 40, below the 70 threshold.
    cust.process(_invoice("N-MID", 10000.0))
    assert notifier.sent == []


def test_high_risk_review_invoice_notifies_even_if_not_rejected():
    notifier = RecordingNotifier()
    cust = Custodian(Ledger(balance=1_000_000), notifier=notifier)
    # large (+25) + round (+15) + short account (+30) = risk 70 -> review, high_risk.
    record = cust.process(_invoice("N-HIGH", 20000.0, vendor_account="AB1"))
    assert record.status is InvoiceStatus.NEEDS_REVIEW
    assert len(notifier.sent) == 1
    assert notifier.sent[0].events == ["high_risk"]


def test_log_notifier_writes_file(tmp_path):
    path = tmp_path / "notifications.jsonl"
    notifier = LogNotifier(path)
    cust = Custodian(Ledger(balance=1_000_000), notifier=notifier)
    cust.process(_invoice(
        "N-LOG", 90000.0, vendor_account="Z1", line_items=[], memo="urgent asap",
    ))
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert "N-LOG" in lines[0]


def test_notification_recorded_in_audit_trail():
    notifier = RecordingNotifier()
    cust = Custodian(Ledger(balance=1_000_000), notifier=notifier)
    record = cust.process(_invoice(
        "N-AUDIT", 80000.0, vendor_account="Q1", line_items=[], memo="wire now",
    ))
    assert any("Notification sent" in step for step in record.audit_trail)
    assert record.status is InvoiceStatus.REJECTED
