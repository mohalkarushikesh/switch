# Custodian — Accounts-Payable Pipeline (End-to-End)

A compact map of how an invoice flows from entry to a persisted decision.
Every step appends to the invoice's **audit trail** — the core governance promise.

## Flow

```mermaid
flowchart TD
    subgraph Entry["Entry points"]
        CLI["CLI<br/>python -m custodian.main"]
        API["FastAPI service<br/>POST /invoices · /batch · /ocr"]
    end

    CLI --> ING
    API --> ING

    ING["<b>IngestAgent</b><br/>raw JSON/OCR → validated Invoice model"]
    ING --> ORCH{{"<b>Custodian</b> orchestrator<br/>process_many → process"}}

    ORCH --> DATA
    subgraph Pipeline["Per-invoice pipeline"]
        direction TB
        DATA["<b>0 · Data</b> (PIIRedactor-Regex/Presidio )<br/>scrub PII before it reaches the LLM"]
        RISK["<b>1 · Risk</b> (RiskAgent-Local/LLM/Heuristic)<br/>score 0–100 · LLM on redacted view, else heuristic"]
        APPR["<b>2 · Approval</b> (ApprovalAgent)<br/>route by risk: auto-pay / review / reject"]
        POL["<b>3 · Policy</b> (PolicyEngine)<br/>hard rules: duplicate, account change, near-dup<br/>can override → block / flag"]
        PAY["<b>4 · Payment</b> (PaymentAgent + Ledger)<br/>release funds for APPROVED only"]
        NOTE["<b>5 · Notify</b><br/>alert on rejected / high-risk"]
        AUD["<b>6 · Audit</b> (AuditLog)<br/>persist full ProcessedInvoice record"]
        DATA --> RISK --> APPR --> POL --> PAY --> NOTE --> AUD
    end

    POL -. "MLflow" .-> TRACK[["ModelTracker<br/>(optional scoring log)"]]
    RISK -..-> TRACK

    AUD --> OUT

    subgraph Outcomes["Final status"]
        direction LR
        PAID(["PAID"])
        REVIEW(["NEEDS_REVIEW"])
        REJECT(["REJECTED"])
        FAILED(["FAILED<br/>approved but insufficient funds"])
    end

    OUT{{"ProcessedInvoice"}}
    OUT --> PAID
    OUT --> REVIEW
    OUT --> REJECT
    OUT --> FAILED

    OUT --> REPORT["CLI report + summary<br/>· or ·<br/>API JSON response"]
```

## Stage cheat-sheet

| # | Stage | Module | Responsibility |
|---|-------|--------|----------------|
| — | Ingest | `agents/ingest.py` | Load & validate invoices (dir of JSON, OCR, or API body) |
| 0 | Data | `governance/data.py` | Redact PII before any LLM call |
| 1 | Risk | `agents/risk.py` + `llm.py` | Fraud/risk score; LLM via LiteLLM or heuristic fallback |
| 2 | Approval | `agents/approval.py` | Risk-based routing decision |
| 3 | Policy | `governance/policy.py`, `dedup.py` | Deterministic rules; can override approval |
| 4 | Payment | `agents/payment.py`, `ledger.py` | Release funds for approved invoices |
| 5 | Notify | `notify.py` | Alert on rejected / high-risk |
| 6 | Audit | `governance/audit.py` | Append-only persisted record |



- A memo (or destination tag) in Ledger is an extra piece of text or numbers required when sending specific cryptocurrencies to a centralized exchange.

- Governance 
  - Duplicate Defection 
  - Vendor Account Change (BEC/Impersonation Detection)
  - Near Duplicate Detection 
  - Amount Validation
  - Absolute Spending Ceiling
  - Blocked Vendors (Denylist)
  - Weak Vendor Account - Vendor account is missing or too short...
  
- Notifier Backends:
    - WebhookNotifier - POST to CUSTODIAN_WEBHOOK_URL
    - LogNotifier - Write to CUSTODIAN_NOTIFY_LOG_PATH
    - MultiNotifier - Chain both
  
- Audit 
  - File-based JSONL (default)
    - AuditLog class
    - One JSON line per invoice, append mode

  - SQLite-based (production)
    - SqliteAuditLog (from src/custodian/db.py)
    - Stores recorded_at, audit_id, full invoice snapshot