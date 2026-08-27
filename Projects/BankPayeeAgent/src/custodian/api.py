"""FastAPI service exposing the Custodian pipeline.

Endpoints:
    GET  /health                 liveness + scoring-mode info
    POST /invoices               submit an invoice, run the pipeline, return the record
    GET  /invoices               list processed invoices (optional ?status= filter)
    GET  /invoices/{invoice_id}  fetch one processed invoice
    GET  /ledger                 current ledger balance + transactions

Run locally:
    PYTHONPATH=src uvicorn custodian.api:app --reload
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .governance import AuditLog
from .ledger import Ledger
from .models import ApprovalDecision, Invoice, InvoiceStatus, ProcessedInvoice
from .orchestrator import Custodian
from .store import InvoiceStore

app = FastAPI(
    title="Custodian — Accounts-Payable Agent API",
    version="0.1.0",
    description="Governed multi-agent pipeline: ingest → risk → approval → auto-pay.",
)

# Static dashboard directory (<project>/ui), served at /ui.
_UI_DIR = Path(__file__).resolve().parents[2] / "ui"

# Shared singletons for the process. A single Custodian keeps one ledger across
# all requests; the store holds every processed record for later lookup.
_ledger = Ledger(balance=settings.ledger_balance)
_audit_log = AuditLog(settings.audit_log_path) if settings.audit_log_path else None
_custodian = Custodian(ledger=_ledger, audit_log=_audit_log)
_store = InvoiceStore()


class InvoiceIn(BaseModel):
    """Invoice payload accepted by POST /invoices (dates as ISO strings)."""

    invoice_id: str
    vendor_name: str
    vendor_account: str
    amount: float
    currency: str = "USD"
    issue_date: date
    due_date: date
    line_items: list[str] = Field(default_factory=list)
    memo: str | None = None


@app.get("/health")
def health() -> dict:
    """Liveness probe plus which scoring path is active."""
    return {
        "status": "ok",
        "scoring_mode": "llm" if settings.has_llm_credentials else "heuristic",
        "model": settings.llm_model,
        "ledger_balance": _ledger.balance,
    }


@app.post("/invoices", response_model=ProcessedInvoice)
def submit_invoice(payload: InvoiceIn) -> ProcessedInvoice:
    """Run one invoice through the pipeline and persist the result."""
    invoice = Invoice(**payload.model_dump())
    record = _custodian.process(invoice)
    _store.save(record)
    return record


@app.post("/invoices/batch", response_model=list[ProcessedInvoice])
def submit_invoices(payloads: list[InvoiceIn]) -> list[ProcessedInvoice]:
    """Run a batch of invoices through the pipeline in one call."""
    records = []
    for payload in payloads:
        record = _custodian.process(Invoice(**payload.model_dump()))
        _store.save(record)
        records.append(record)
    return records


@app.get("/invoices", response_model=list[ProcessedInvoice])
def list_invoices(
    status: str | None = None,
    min_risk: int | None = None,
    max_risk: int | None = None,
) -> list[ProcessedInvoice]:
    """List processed invoices, filterable by status and risk-score range."""
    records = _store.list(status=status)
    if min_risk is not None:
        records = [r for r in records if r.assessment and r.assessment.risk_score >= min_risk]
    if max_risk is not None:
        records = [r for r in records if r.assessment and r.assessment.risk_score <= max_risk]
    return records


@app.get("/invoices/{invoice_id}", response_model=ProcessedInvoice)
def get_invoice(invoice_id: str) -> ProcessedInvoice:
    """Fetch a single processed invoice by id."""
    record = _store.get(invoice_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found.")
    return record


@app.post("/invoices/{invoice_id}/approve", response_model=ProcessedInvoice)
def approve_invoice(invoice_id: str) -> ProcessedInvoice:
    """Human reviewer approves a queued invoice; payment is then attempted."""
    record = _store.get(invoice_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found.")
    if record.status is not InvoiceStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=409,
            detail=f"Only invoices in 'needs_review' can be approved (was {record.status.value}).",
        )

    decision = ApprovalDecision(
        status=InvoiceStatus.APPROVED,
        reason="Manually approved by reviewer.",
        requires_human=False,
    )
    record.decision = decision
    payment = _custodian.payment.pay(record.invoice, decision)
    record.payment = payment
    if payment.paid:
        record.status = InvoiceStatus.PAID
        record.audit_trail.append(
            f"Manually approved by reviewer; payment released: {payment.transaction_id}."
        )
    else:
        record.status = InvoiceStatus.FAILED
        record.audit_trail.append(
            f"Manually approved by reviewer but payment failed: {payment.reason}"
        )
    _store.save(record)
    return record


@app.post("/invoices/{invoice_id}/reject", response_model=ProcessedInvoice)
def reject_invoice(invoice_id: str) -> ProcessedInvoice:
    """Human reviewer rejects a queued invoice; no payment is made."""
    record = _store.get(invoice_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found.")
    if record.status is not InvoiceStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=409,
            detail=f"Only invoices in 'needs_review' can be rejected (was {record.status.value}).",
        )

    record.decision = ApprovalDecision(
        status=InvoiceStatus.REJECTED,
        reason="Manually rejected by reviewer.",
        requires_human=False,
    )
    record.status = InvoiceStatus.REJECTED
    record.audit_trail.append("Manually rejected by reviewer.")
    _store.save(record)
    return record


@app.get("/ledger")
def get_ledger() -> dict:
    """Return the current ledger balance and its recorded transactions."""
    return {
        "balance": _ledger.balance,
        "transactions": [t.__dict__ for t in _ledger.transactions],
    }


@app.get("/stats")
def stats() -> dict:
    """Aggregate summary across all processed invoices."""
    records = _store.list()
    by_status: dict[str, int] = {}
    for r in records:
        by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
    total_paid = sum(
        r.invoice.amount for r in records if r.status is InvoiceStatus.PAID
    )
    return {
        "total_invoices": len(records),
        "by_status": by_status,
        "total_paid": total_paid,
        "ledger_balance": _ledger.balance,
    }


@app.get("/policies")
def policies() -> dict:
    """Expose the active policy-governance configuration."""
    return {
        "absolute_ceiling": _custodian.policy.max_amount,
        "blocked_vendors": sorted(_custodian.policy.blocked_vendors),
        "auto_pay_max_risk": settings.auto_pay_max_risk,
        "auto_pay_max_amount": settings.auto_pay_max_amount,
        "reject_min_risk": settings.reject_min_risk,
    }


@app.get("/audit")
def audit() -> dict:
    """Return the persisted audit log, if one is configured."""
    if _audit_log is None:
        raise HTTPException(
            status_code=404,
            detail="No audit log configured (set CUSTODIAN_AUDIT_LOG).",
        )
    return {"path": str(_audit_log.path), "entries": _audit_log.read_all()}


@app.get("/")
def root() -> RedirectResponse:
    """Send the bare root to the dashboard."""
    return RedirectResponse(url="/ui/")


# Serve the static dashboard last so it doesn't shadow the API routes above.
if _UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
