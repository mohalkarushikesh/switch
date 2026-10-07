## **Complete End-to-End Invoice Journey Through Custodian AP System**

### **System Overview**
The Custodian AP platform is a **multi-agent AI system** that processes invoices through a governed pipeline with 6 governance layers. Let me trace a single invoice's complete journey:

---

## **1️⃣ INVOICE INGESTION (Entry Point)**

### **File:** `src/custodian/agents/ingest.py` → `IngestAgent` class

**Methods:**
- `from_dict(raw: dict)` - validates raw JSON into Invoice model
- `from_text(text: str)` - parses OCR-style text into Invoice
- `from_file(path)` - loads from JSON file
- `_coerce_dates(raw)` - converts ISO date strings to date objects

**API Entry Points** (`src/custodian/api.py`):
- `POST /invoices` - direct JSON submission
- `POST /invoices/ocr` - OCR text input
- `POST /invoices/batch` - bulk submission

**Process:**
```
User submits invoice → IngestAgent.from_dict() → validates against Invoice model
                    → checks required fields (invoice_id, vendor_name, amount, etc.)
                    → date coercion (ISO strings → date objects)
                    → returns validated Invoice object
```

**Output Model** (`src/custodian/models.py`):
```python
class Invoice:
    invoice_id: str
    vendor_name: str
    vendor_account: str          # payment destination
    amount: float
    currency: str = "INR"
    issue_date: date
    due_date: date
    line_items: list[str]
    memo: str | None
```

---

## **2️⃣ OCR PROCESSING (Optional Path)**

### **File:** `src/custodian/ocr.py` → `parse_invoice_text(text: str)`

**Purpose:** Extract structured fields from raw OCR text using regex patterns

**Field Extraction:**
- `invoice_id` - pattern: `invoice\s*(?:id|no\.?|number|#)\s*[:#]`
- `vendor_name` - pattern: `(?:vendor|supplier|bill\s*from)`
- `vendor_account` - pattern: `(?:account|acct|iban)`
- `amount` - pattern: `(?:grand\s*total|amount|total)` with currency symbols
- `issue_date` / `due_date` - pattern: `\d{4}-\d{2}-\d{2}` (ISO format)
- `line_items` - extracted from bullet points (`-` or `*`)
- `memo` - narrative/notes field

**PII Handling in OCR:**
- Personal data lines (name, DOB, gender) are folded into memo so they pass through PII redaction
- Prevents silent data leakage

**Output:** Dictionary → passed to `IngestAgent.from_dict()` for validation

---

## **3️⃣ CORE PIPELINE ORCHESTRATION**

### **File:** `src/custodian/orchestrator.py` → `Custodian.process()` method

This is the **main orchestration engine** that chains all agents and governance layers.

### **Step A: Create Record & Initialize**
```python
record = ProcessedInvoice(
    invoice=invoice, 
    status=InvoiceStatus.RECEIVED
)
record.audit_trail.append(f"Ingested invoice {invoice.invoice_id}...")
```
**Status:** `RECEIVED`

---

### **Step B: DATA GOVERNANCE LAYER (PII Redaction)**

### **File:** `src/custodian/governance/data.py` → `PIIRedactor` class

**Flow:**
```
invoice → redactor.redact_invoice()
    ↓
memo, line_items → redact_text() (PII backend: regex or Presidio)
    ↓
Found PII types (EMAIL, SSN, IBAN, PHONE, PERSON, etc.)
    ↓
Return: (redacted_invoice, [pii_types_found])
    ↓
audit_trail += "Data layer: redacted PII types [PHONE, EMAIL] before LLM"
```

**PII Backends:**

1. **Regex Backend** (default, no dependencies)
   - Pattern-based detection for EMAIL, SSN, IBAN, CREDIT_CARD, PHONE
   - Labeled patterns for PERSON, GENDER, DOB
   - Fast, deterministic, offline

2. **Presidio Backend** (opt-in via `CUSTODIAN_PII_BACKEND=presidio`)
   - NLP-based using spaCy model
   - Falls back to regex if Presidio unavailable
   - More contextual (e.g., recognizes "John" in context as PERSON)

**Protected Fields:** Only `memo` and `line_items`; structural fields (vendor_name, amount, account) are left intact for scoring

**Output:** `ProcessedInvoice.redacted_pii` contains list of PII entity types found

---

### **Step C: RISK SCORING AGENT**

### **File:** `src/custodian/agents/risk.py` → `RiskAgent.assess()` method

**Three-Tier Fallback Chain:**

#### **Tier 1: Local Model** (if `CUSTODIAN_LOCAL_MODEL` is set)
- **File:** `src/custodian/local_llm.py` → `score_invoice_locally()`
- On-device transformer model (offline, no cost)
- If available and returns result → use it, skip Tiers 2 & 3

#### **Tier 2: API LLM via LiteLLM** (if provider key configured)
- **File:** `src/custodian/llm.py` → `score_invoice_with_llm()`

**Process:**
1. Build system prompt + user prompt
2. Route to provider based on model name prefix:
   - `gpt-4o-mini` → OpenAI (uses `OPENAI_API_KEY`)
   - `groq/llama-3.1-8b-instant` → Groq (uses `GROQ_API_KEY`)
   - `huggingface/...` → Hugging Face (uses `HUGGINGFACE_API_KEY`)
   - `anthropic/claude-opus...` → Anthropic (uses `ANTHROPIC_API_KEY`)

3. LLM Prompt:
```python
_SYSTEM_PROMPT = """You are a bank's accounts-payable fraud & risk analyst.
Assess the given invoice and respond with ONLY a JSON object:
{"risk_score": <int 0-100>, "fraud_flags": [<short strings>], "rationale": "<explanation>"}
"""

_build_user_prompt(invoice) returns:
"""Invoice ID: INV-001
Vendor: ACME Corp
Vendor account: 123456789
Amount: 50000 INR
Issued: 2025-01-15 | Due: 2025-01-20
Line items: Software license, Support
Memo: Urgent payment needed
"""
```

4. Error Handling:
   - Transient errors (rate-limit, 5xx, timeout) → retry up to `llm_max_retries`
   - Permanent errors (bad key, unknown model) → no retry, fall through
   - Parse failures → fall through to heuristic

5. **Outcome Tracking** (exported to `/metrics`):
   - `llm_success` - parseable assessment returned
   - `llm_failed` - call raised exception
   - `llm_unparseable` - returned, but no valid JSON
   - `not_configured` - no key/credentials

#### **Tier 3: Heuristic Fallback** (always available)
- **File:** `src/custodian/agents/risk.py` → `_heuristic()` method

**Heuristic Scoring Rules** (each adds points):
```python
score = 0
flags = []

if amount >= 50_000:
    score += 45
    flags.append("very large amount")
elif amount >= 10_000:
    score += 25
    flags.append("large amount")

if amount >= 1_000 and amount % 1_000 == 0:
    score += 15
    flags.append("round amount")  # suspicious fabrication signal

if not vendor_account or len(vendor_account) < 6:
    score += 30
    flags.append("missing/short vendor account")

memo = (invoice.memo or "").lower()
if any(word in memo for word in ("urgent", "asap", "immediately", "wire now")):
    score += 20
    flags.append("urgency language in memo")  # social engineering signal

if not line_items:
    score += 15
    flags.append("no line items")

if due_date < issue_date:
    score += 25
    flags.append("due date precedes issue date")  # data integrity issue

score = min(100, score)  # cap at 100
```

**Output:** `RiskAssessment` model
```python
class RiskAssessment:
    risk_score: int              # 0-100
    fraud_flags: list[str]       # reasons for the score
    rationale: str               # human explanation
    source: str                  # "local-llm", "llm", or "heuristic"
```

**Audit Trail Entry:**
```
"Risk scored 35/100 via llm. Flags: ['large amount', 'urgency language']."
```

**Record Update:**
```
record.assessment = assessment
record.status = InvoiceStatus.SCORED
```

---

### **Step D: APPROVAL ROUTING AGENT**

### **File:** `src/custodian/agents/approval.py` → `ApprovalAgent.decide()` method

**Decision Logic** (based on risk_score + amount):

```python
score = assessment.risk_score

# 1. Too risky → reject outright
if score >= settings.reject_min_risk:  # e.g., 75
    return ApprovalDecision(
        status=InvoiceStatus.REJECTED,
        reason=f"Risk score {score} >= reject threshold {settings.reject_min_risk}.",
        requires_human=False
    )

# 2. Safe to auto-pay (low risk + under amount cap)
if (score <= settings.auto_pay_max_risk         # e.g., 30
    and amount <= settings.auto_pay_max_amount):  # e.g., 100,000
    return ApprovalDecision(
        status=InvoiceStatus.APPROVED,
        reason=f"Risk score {score} <= {settings.auto_pay_max_risk} and amount...",
        requires_human=False
    )

# 3. In-between → route to human
return ApprovalDecision(
    status=InvoiceStatus.NEEDS_REVIEW,
    reason="Risk score or amount exceeds auto-pay limits; human review required.",
    requires_human=True
)
```

**Output Status:**
- `APPROVED` - safe to auto-pay
- `REJECTED` - too risky, will not pay
- `NEEDS_REVIEW` - human approval required

**Audit Trail Entry:**
```
"Approval decision: NEEDS_REVIEW — Risk score 52 or amount 75000 exceeds auto-pay limits."
```

**Record Update:**
```
record.decision = decision
record.status = decision.status  # (may still change via policy)
```

---

### **Step E: POLICY GOVERNANCE LAYER**

### **File:** `src/custodian/governance/policy.py` → `PolicyEngine.evaluate()` method

**Purpose:** Deterministic hard rules that can **override** the risk-based approval decision

**Rule Checks:**

#### **1. Duplicate Detection**
```python
if is_duplicate:  # Same invoice_id already processed
    violations.append(PolicyViolation(
        code="duplicate_invoice",
        severity="block",  # FORCE REJECT
        message=f"Invoice id '{invoice.invoice_id}' was already processed."
    ))
```

#### **2. Vendor Account Change (BEC/Impersonation Detection)**
```python
if account_changed:  # Vendor paid before, but NEW payee account
    violations.append(PolicyViolation(
        code="vendor_account_changed",
        severity="flag",  # FORCE HUMAN REVIEW
        message="Vendor was paid before, but payee account is new..."
    ))
```

#### **3. Near-Duplicate Detection**
```python
if near_duplicate:  # Same vendor, very similar amount/dates
    violations.append(PolicyViolation(
        code="possible_duplicate",
        severity="flag",  # FORCE HUMAN REVIEW
        message=f"Resembles invoice '{near_duplicate.invoice_id}'..."
    ))
```

#### **4. Amount Validation**
```python
if invoice.amount <= 0:
    violations.append(PolicyViolation(
        code="non_positive_amount",
        severity="block"
    ))
```

#### **5. Absolute Spending Ceiling**
```python
if invoice.amount > self.max_amount:  # e.g., 500,000
    violations.append(PolicyViolation(
        code="exceeds_absolute_ceiling",
        severity="block",
        message=f"Amount {invoice.amount} exceeds absolute ceiling {self.max_amount}."
    ))
```

#### **6. Blocked Vendors (Denylist)**
```python
if invoice.vendor_name.lower() in self.blocked_vendors:
    violations.append(PolicyViolation(
        code="blocked_vendor",
        severity="block",
        message=f"Vendor '{invoice.vendor_name}' is on the deny list."
    ))
```

#### **7. Weak Vendor Account**
```python
if not invoice.vendor_account or len(invoice.vendor_account) < 6:
    violations.append(PolicyViolation(
        code="weak_vendor_account",
        severity="flag",  # FORCE HUMAN REVIEW
        message="Vendor account is missing or too short..."
    ))
```

**Override Logic:**
```python
# Separate violations by severity
blocks = [v for v in violations if v.severity == "block"]
flags = [v for v in violations if v.severity == "flag"]

# Block violations override approval decision → REJECT
if blocks:
    decision = ApprovalDecision(
        status=InvoiceStatus.REJECTED,
        reason=f"Blocked by policy: {', '.join(v.code for v in blocks)}.",
        requires_human=False
    )
    record.audit_trail.append(f"Policy override → rejected ({len(blocks)} blocking violation(s)).")

# Flag violations override APPROVED only → NEEDS_REVIEW
elif flags and decision.status is InvoiceStatus.APPROVED:
    decision = ApprovalDecision(
        status=InvoiceStatus.NEEDS_REVIEW,
        reason=f"Flagged by policy: {', '.join(v.code for v in flags)}.",
        requires_human=True
    )
    record.audit_trail.append("Policy override → routed to human review.")
```

**Record Update:**
```
record.policy_violations = violations
record.decision = decision  # (now overridden if violations exist)
record.status = decision.status
```

---

### **Step F: DUPLICATE & VENDOR ACCOUNT CHANGE DETECTION**

### **File:** `src/custodian/governance/dedup.py`

**Called from API** (`_run_pipeline()` in `api.py`):
```python
# Check if invoice_id already exists in store
is_duplicate = _store.has(invoice.invoice_id)

# Check if vendor has been paid before with different account
known_accounts = _store.known_vendor_accounts(invoice.vendor_name)
account_changed = bool(known_accounts) and invoice.vendor_account not in known_accounts

# Find near-duplicates (same vendor, similar amount/dates)
near_duplicate = find_near_duplicate(
    invoice,
    _store.invoices_by_vendor(invoice.vendor_name),
    threshold=settings.dedup_threshold  # e.g., 0.85 similarity
)

# Pass all three signals to Custodian.process()
record = _custodian.process(
    invoice,
    is_duplicate=is_duplicate,
    account_changed=account_changed,
    near_duplicate=near_duplicate
)
```

---

### **Step G: PAYMENT EXECUTION**

### **File:** `src/custodian/agents/payment.py` → `PaymentAgent.pay()` method

**Conditions to Pay:**
1. Decision status must be `APPROVED`
2. Ledger must have sufficient balance

**Process:**
```python
# Guard 1: Only pay APPROVED invoices
if decision.status is not InvoiceStatus.APPROVED:
    return PaymentResult(
        paid=False,
        transaction_id=None,
        reason=f"Not approved for payment (status={decision.status.value})."
    )

# Guard 2: Check ledger balance
if not self.ledger.can_cover(invoice.amount):
    return PaymentResult(
        paid=False,
        transaction_id=None,
        reason="Insufficient ledger balance."
    )

# Execute payment
txn = self.ledger.pay(
    invoice_id=invoice.invoice_id,
    vendor_account=invoice.vendor_account,
    amount=invoice.amount,
    currency=invoice.currency
)

return PaymentResult(
    paid=True,
    transaction_id=txn.transaction_id,
    reason=f"Paid {invoice.amount} {invoice.currency} to {invoice.vendor_account}."
)
```

**Ledger File:** `src/custodian/ledger.py` → `Ledger` class

**Ledger Operations:**
```python
class Ledger:
    balance: float  # Running balance
    transactions: list[Transaction]  # All payments

    def can_cover(amount) → bool
    def pay(invoice_id, vendor_account, amount, currency) → Transaction
    def reverse(invoice_id) → float  # Refund if deleted
```

**Record Update:**
```
if payment.paid:
    record.status = InvoiceStatus.PAID
    record.audit_trail.append(
        f"Payment released: {payment.transaction_id} — {payment.reason}"
    )
else:
    record.status = InvoiceStatus.FAILED
    record.audit_trail.append(f"Payment failed: {payment.reason}")

record.payment = payment
```

---

### **Step H: NOTIFICATIONS (Optional)**

### **File:** `src/custodian/notify.py`

**Trigger:** High-risk or rejected invoices

**Notifier Backends:**
1. **WebhookNotifier** - POST to `CUSTODIAN_WEBHOOK_URL`
2. **LogNotifier** - Write to `CUSTODIAN_NOTIFY_LOG_PATH`
3. **MultiNotifier** - Chain both

**Notification Data:**
```python
class Notification:
    invoice_id: str
    events: list[str]  # ["rejected", "high_risk"]
    status: str        # final status
    risk_score: int
    vendor_name: str
    amount: float
    message: str       # human-readable
```

**Audit Trail Entry:**
```
"Notification sent (rejected, high_risk)."
```

---

### **Step I: AUDIT LOGGING**

### **File:** `src/custodian/governance/audit.py` → `AuditLog` class

**Purpose:** Append-only record of every processed invoice for regulatory compliance

**Backends:**
1. **File-based JSONL** (default)
   - `AuditLog` class
   - One JSON line per invoice, append mode

2. **SQLite-based** (production)
   - `SqliteAuditLog` (from `src/custodian/db.py`)
   - Stores `recorded_at`, `audit_id`, full invoice snapshot

**Process:**
```python
if self.audit_log is not None:
    self.audit_log.record(record)
```

**Recorded Data (ProcessedInvoice):**
```python
ProcessedInvoice(
    invoice=Invoice(...),
    status=InvoiceStatus.PAID,
    assessment=RiskAssessment(...),
    decision=ApprovalDecision(...),
    payment=PaymentResult(...),
    redacted_pii=[...],
    policy_violations=[...],
    audit_trail=[...]  # Complete decision history
)
```

**Audit Trail Format:**
Full step-by-step record:
```
[
  "Ingested invoice INV-001 from 'ACME Corp' for 50000 INR.",
  "Data layer: redacted PII types ['PHONE', 'EMAIL'] before LLM.",
  "Risk scored 45/100 via llm. Flags: ['large amount', 'urgency language'].",
  "Approval decision: NEEDS_REVIEW — Risk score 45 or amount 50000 exceeds auto-pay limits.",
  "Policy [flag] vendor_account_changed: Vendor was paid before, but payee account...",
  "Policy override → routed to human review.",
  "Notification sent (high_risk)."
]
```

**Persistence:**
- Records survive application restarts
- Auditable trail for compliance/disputes
- Used to reconstruct ledger on startup

---

## **2️⃣ HUMAN REVIEW FLOW**

### **File:** `src/custodian/api.py`

**Endpoint: `POST /invoices/{invoice_id}/approve`**
```python
@app.post("/invoices/{invoice_id}/approve")
def approve_invoice(invoice_id: str, _=Depends(require_role("reviewer"))) → ProcessedInvoice:
    record = _store.get(invoice_id)
    if record.status is not InvoiceStatus.NEEDS_REVIEW:
        raise HTTPException(409, "Only invoices in 'needs_review' can be approved")
    
    # Manually override decision
    decision = ApprovalDecision(
        status=InvoiceStatus.APPROVED,
        reason="Manually approved by reviewer.",
        requires_human=False,
    )
    
    # Try to pay (same checks as auto-pay)
    payment = _custodian.payment.pay(record.invoice, decision)
    
    if payment.paid:
        record.status = InvoiceStatus.PAID
        record.audit_trail.append(
            f"Manually approved by reviewer; payment released: {payment.transaction_id}."
        )
    else:
        record.status = InvoiceStatus.FAILED
        record.audit_trail.append(f"Manually approved but payment failed: {payment.reason}")
    
    _store.save(record)
    _audit_log.record(record)
    return record
```

**Endpoint: `POST /invoices/{invoice_id}/reject`**
```python
@app.post("/invoices/{invoice_id}/reject")
def reject_invoice(invoice_id: str, _=Depends(require_role("reviewer"))) → ProcessedInvoice:
    record = _store.get(invoice_id)
    if record.status is not InvoiceStatus.NEEDS_REVIEW:
        raise HTTPException(409, "Only invoices in 'needs_review' can be rejected")
    
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
```

---

## **3️⃣ INVOICE LIFECYCLE STATES**

```
RECEIVED → SCORED → [APPROVED | NEEDS_REVIEW | REJECTED]
                        ↓
                   [PAID | FAILED]
```

| Status | Meaning | Auto-transition? |
|--------|---------|------------------|
| `RECEIVED` | Ingested, not yet scored | No |
| `SCORED` | Risk assessment complete | No (moves to approval status) |
| `APPROVED` | Cleared for auto-pay | No (moves to PAID/FAILED on pay()) |
| `NEEDS_REVIEW` | Routed to human | No (waits for /approve or /reject) |
| `REJECTED` | Blocked (too risky or policy violation) | No (terminal) |
| `PAID` | Payment released successfully | No (terminal) |
| `FAILED` | Approved but payment couldn't execute | No (terminal) |

---

## **4️⃣ DATA PERSISTENCE**

### **File:** `src/custodian/db.py` → `Database`, `SqliteStore`, `SqliteAuditLog`

**SQLite Schema:**
```sql
-- Processed invoices
invoices
  id (TEXT PRIMARY KEY) = invoice_id
  data (JSON) = full ProcessedInvoice
  status (TEXT)
  risk_score (INTEGER)
  created_at (TIMESTAMP)
  
-- Audit trail
audit_log
  id (INTEGER PRIMARY KEY)
  invoice_id (TEXT FOREIGN KEY)
  recorded_at (TIMESTAMP)
  event_data (JSON) = ProcessedInvoice snapshot
```

**Startup Behavior:**
```python
def _rebuild_ledger() → Ledger:
    ledger = Ledger(balance=settings.ledger_balance)
    # Reconstruct balance from all PAID invoices
    for record in _store.list(status=InvoiceStatus.PAID.value):
        ledger.balance -= record.invoice.amount
        ledger.transactions.append(record.payment.transaction_id)
    return ledger
```

This ensures ledger consistency across restarts.

---

## **5️⃣ COMPLETE FLOW SUMMARY**

### **Happy Path (Auto-Paid Invoice):**
```
1. Invoice submitted (JSON or OCR text)
   ↓
2. IngestAgent validates → Invoice model
   ↓
3. PIIRedactor scrubs memo/line_items
   ↓
4. RiskAgent scores (LLM or heuristic) → 20/100 (low risk)
   ↓
5. ApprovalAgent routes → APPROVED (low score + under amount limit)
   ↓
6. PolicyEngine checks → no violations
   ↓
7. PaymentAgent executes → payment released
   ↓
8. Status: PAID
   ↓
9. AuditLog records complete trail
   ↓
10. Database persists record + ledger updated
```

### **Policy-Blocked Invoice:**
```
1-5. [Same as above up to PaymentAgent]
   But policy detects duplicate_invoice (severity="block")
   ↓
6. PolicyEngine overrides decision → status = REJECTED
   ↓
7. PaymentAgent skips payment (not APPROVED)
   ↓
8. Status: REJECTED
   ↓
9. Notifier sends webhook/log
   ↓
10. AuditLog records
```

### **Human-Review Path:**
```
1-5. [Invoice scored and routed to NEEDS_REVIEW]
   ↓
6. Reviewer fetches invoice from /invoices/{id}
   ↓
7. Reviewer decides: /invoices/{id}/approve or /reject
   ↓
8. If approve: payment executes (same checks), status = PAID/FAILED
   If reject: status = REJECTED
   ↓
9. AuditLog records reviewer action + outcome
```

---

## **6️⃣ GOVERNANCE LAYERS SUMMARY**

| Layer | File | Responsibility | Observable |
|-------|------|-----------------|-----------|
| **Identity** | (not yet implemented) | Auth (API keys, roles) | `require_role()` decorator |
| **Data** | `governance/data.py` | PII redaction | `record.redacted_pii` |
| **Model** | `llm.py`, `local_llm.py` | Risk scoring | `record.assessment.source` |
| **Policy** | `governance/policy.py` | Business rules | `record.policy_violations` |
| **Agent Runtime** | `orchestrator.py` | Execution + chaining | `record.status` transitions |
| **Operations** | `governance/audit.py` | Audit trail + metrics | `/audit`, `/metrics` endpoints |

---

## **7️⃣ API ENDPOINTS SUMMARY**

| Method | Path | Purpose | Stage |
|--------|------|---------|-------|
| `POST` | `/invoices` | Submit JSON | Ingest |
| `POST` | `/invoices/ocr` | Submit OCR text | Ingest |
| `POST` | `/invoices/batch` | Bulk submit | Ingest |
| `GET` | `/invoices` | List all | Query |
| `GET` | `/invoices/{id}` | Fetch one | Query |
| `POST` | `/invoices/{id}/approve` | Human approve | Review |
| `POST` | `/invoices/{id}/reject` | Human reject | Review |
| `DELETE` | `/invoices/{id}` | Delete (refund if paid) | Admin |
| `GET` | `/ledger` | Balance + transactions | Reporting |
| `GET` | `/audit` | Audit trail (with limit) | Reporting |
| `GET` | `/policies` | Active governance config | Reporting |
| `GET` | `/metrics` | Prometheus format | Observability |
| `GET` | `/health` | Liveness + scoring mode | Ops |

---

## **Key Files Map**

```
src/custodian/
├── orchestrator.py       ← Main pipeline (Custodian.process())
├── models.py             ← Data models (Invoice, ProcessedInvoice, etc.)
├── api.py                ← FastAPI endpoints + entry points
├── config.py             ← Settings from env/.env
├── db.py                 ← SQLite persistence
├── ledger.py             ← Payment rail + balance tracking
├── llm.py                ← LiteLLM wrapper (OpenAI/Groq/HF/Anthropic)
├── local_llm.py          ← On-device model scoring
├── ocr.py                ← OCR text → structured fields
├── notify.py             ← Notifications (webhook/log)
├── tracking.py           ← MLflow model tracking
├── agents/
│   ├── ingest.py         ← Invoice validation
│   ├── risk.py           ← Risk scoring (local/llm/heuristic)
│   ├── approval.py       ← Approval routing (risk-based thresholds)
│   └── payment.py        ← Payment execution
└── governance/
    ├── data.py           ← PII redaction (regex/presidio)
    ├── policy.py         ← Business rules (duplicates, account changes, etc.)
    ├── audit.py          ← Append-only audit log
    └── dedup.py          ← Duplicate + near-duplicate detection
```

---

This is the **complete, detailed, file-wise end-to-end journey** of a single invoice through the Custodian AP system, with every function, method, model, and governance checkpoint mapped to its source file.