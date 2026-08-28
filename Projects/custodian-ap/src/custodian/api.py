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

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agents import IngestAgent
from .config import settings
from .db import Database, SqliteAuditLog, SqliteStore
from .ledger import Ledger, Transaction
from .models import ApprovalDecision, Invoice, InvoiceStatus, ProcessedInvoice
from .notify import LogNotifier, MultiNotifier, Notifier, WebhookNotifier
from .orchestrator import Custodian
from .tracking import build_tracker

app = FastAPI(
    title="Custodian — Accounts-Payable Agent API",
    version="0.1.0",
    description="Governed multi-agent pipeline: ingest → risk → approval → auto-pay.",
)

# Static dashboards: the zero-build one at /ui, and the built React app at /app.
_UI_DIR = Path(__file__).resolve().parents[2] / "ui"
_WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"

# Shared singletons. Persistence is backed by SQLite so processed invoices and
# the audit trail survive restarts.
_db = Database(settings.db_path)
_store = SqliteStore(_db)
_audit_log = SqliteAuditLog(_db)


def _rebuild_ledger() -> Ledger:
    """Reconstruct ledger balance + transactions from persisted paid invoices.

    Keeps the balance consistent with the durable store across restarts.
    """
    ledger = Ledger(balance=settings.ledger_balance)
    for record in _store.list(status=InvoiceStatus.PAID.value):
        ledger.balance -= record.invoice.amount
        if record.payment and record.payment.transaction_id:
            ledger.transactions.append(Transaction(
                transaction_id=record.payment.transaction_id,
                invoice_id=record.invoice.invoice_id,
                vendor_account=record.invoice.vendor_account,
                amount=record.invoice.amount,
                currency=record.invoice.currency,
            ))
    return ledger


def _build_notifier() -> Notifier | None:
    """Assemble a notifier from config (webhook and/or log); None if unconfigured."""
    notifiers: list[Notifier] = []
    if settings.webhook_url:
        notifiers.append(WebhookNotifier(settings.webhook_url))
    if settings.notify_log_path:
        notifiers.append(LogNotifier(settings.notify_log_path))
    if not notifiers:
        return None
    return notifiers[0] if len(notifiers) == 1 else MultiNotifier(notifiers)


_ledger = _rebuild_ledger()
_custodian = Custodian(
    ledger=_ledger,
    audit_log=_audit_log,
    notifier=_build_notifier(),
    tracker=build_tracker(settings.mlflow_tracking_uri, settings.mlflow_experiment),
)


# --- Authentication -------------------------------------------------------
# API keys map to roles. "admin" may do anything; other roles are scoped.
# When no keys are configured, auth is disabled and all endpoints are open
# (keeps the local demo and tests friction-free). Reads stay open by design in
# this MVP; only state-changing endpoints are protected.

def _parse_api_keys(raw: str) -> dict[str, str]:
    keys: dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        key, _, role = pair.partition(":")
        keys[key.strip()] = (role.strip() or "admin")
    return keys


_API_KEYS = _parse_api_keys(settings.api_keys)


def require_role(*allowed: str):
    """Build a dependency that authenticates the X-API-Key and checks its role."""

    def dependency(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> dict:
        if not _API_KEYS:                       # auth disabled — open
            return {"role": "admin", "auth": "disabled"}
        if not x_api_key or x_api_key not in _API_KEYS:
            raise HTTPException(status_code=401, detail="Missing or invalid API key.")
        role = _API_KEYS[x_api_key]
        if allowed and role != "admin" and role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' not permitted; requires one of {list(allowed)}.",
            )
        return {"role": role}

    return dependency


class InvoiceIn(BaseModel):
    """Invoice payload accepted by POST /invoices (dates as ISO strings)."""

    invoice_id: str
    vendor_name: str
    vendor_account: str
    amount: float
    currency: str = "INR"
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
def submit_invoice(payload: InvoiceIn, _=Depends(require_role("submitter"))) -> ProcessedInvoice:
    """Run one invoice through the pipeline and persist the result.

    A re-submitted invoice id is flagged as a duplicate (blocked by policy) and
    does NOT overwrite the original record — only the attempt is audited.
    """
    invoice = Invoice(**payload.model_dump())
    is_duplicate = _store.has(invoice.invoice_id)
    record = _custodian.process(invoice, is_duplicate=is_duplicate)
    if not is_duplicate:
        _store.save(record)
    return record


class OCRIn(BaseModel):
    """Raw invoice text, as produced by an OCR engine or vision model."""

    text: str


@app.post("/invoices/ocr", response_model=ProcessedInvoice)
def submit_ocr(payload: OCRIn, _=Depends(require_role("submitter"))) -> ProcessedInvoice:
    """Extract an invoice from OCR text, then run it through the pipeline."""
    try:
        invoice = IngestAgent().from_text(payload.text)
    except Exception as exc:  # validation / extraction failure
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract a valid invoice from the text: {exc}",
        )
    is_duplicate = _store.has(invoice.invoice_id)
    record = _custodian.process(invoice, is_duplicate=is_duplicate)
    if not is_duplicate:
        _store.save(record)
    return record


@app.post("/invoices/batch", response_model=list[ProcessedInvoice])
def submit_invoices(payloads: list[InvoiceIn], _=Depends(require_role("submitter"))) -> list[ProcessedInvoice]:
    """Run a batch of invoices through the pipeline in one call."""
    records = []
    for payload in payloads:
        invoice = Invoice(**payload.model_dump())
        is_duplicate = _store.has(invoice.invoice_id)
        record = _custodian.process(invoice, is_duplicate=is_duplicate)
        if not is_duplicate:
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
def approve_invoice(invoice_id: str, _=Depends(require_role("reviewer"))) -> ProcessedInvoice:
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
    _audit_log.record(record)
    return record


@app.post("/invoices/{invoice_id}/reject", response_model=ProcessedInvoice)
def reject_invoice(invoice_id: str, _=Depends(require_role("reviewer"))) -> ProcessedInvoice:
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
    _audit_log.record(record)
    return record


@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: str, _=Depends(require_role("admin"))) -> dict:
    """Delete a processed invoice (admin only).

    If it was paid, the ledger is refunded so the balance stays consistent with
    the remaining invoices.
    """
    record = _store.get(invoice_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found.")

    refunded = 0.0
    if record.status is InvoiceStatus.PAID:
        refunded = _ledger.reverse(invoice_id)
    _store.delete(invoice_id)
    return {"deleted": invoice_id, "refunded": refunded}


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


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    """Prometheus text-format metrics for the observability stack to scrape."""
    records = _store.list()
    by_status: dict[str, int] = {}
    for r in records:
        by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
    total_paid = sum(r.invoice.amount for r in records if r.status is InvoiceStatus.PAID)

    lines = [
        "# HELP custodian_invoices_total Total invoices processed.",
        "# TYPE custodian_invoices_total counter",
        f"custodian_invoices_total {len(records)}",
        "# HELP custodian_invoices_by_status Invoices grouped by final status.",
        "# TYPE custodian_invoices_by_status gauge",
    ]
    for status_value, count in sorted(by_status.items()):
        lines.append(f'custodian_invoices_by_status{{status="{status_value}"}} {count}')
    lines += [
        "# HELP custodian_total_paid_amount Total amount auto-paid.",
        "# TYPE custodian_total_paid_amount counter",
        f"custodian_total_paid_amount {total_paid}",
        "# HELP custodian_ledger_balance Current mock-ledger balance.",
        "# TYPE custodian_ledger_balance gauge",
        f"custodian_ledger_balance {_ledger.balance}",
    ]
    return "\n".join(lines) + "\n"


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
    """Send the bare root to the richer React app if built, else the simple UI."""
    return RedirectResponse(url="/app/" if _WEB_DIST.exists() else "/ui/")


# Serve the dashboards last so they don't shadow the API routes above.
# /ui  = zero-build single-file dashboard (always present)
# /app = built React app (present after `cd web && npm run build`)
if _UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
if _WEB_DIST.exists():
    app.mount("/app", StaticFiles(directory=str(_WEB_DIST), html=True), name="app")
