"""CLI entrypoint: run the sample invoices through Custodian and print a report.

Usage (from the project root):
    python -m custodian.main                 # uses data/sample_invoices/
    python -m custodian.main path/to/dir     # a directory of invoice JSON files
"""

from __future__ import annotations

import sys
from pathlib import Path

from .agents import IngestAgent                                                            # Imports modules → Loads required classes (IngestAgent, Custodian, AuditLog, etc.).
from .config import settings
from .governance import AuditLog
from .models import InvoiceStatus, ProcessedInvoice
from .orchestrator import Custodian

# Default sample data lives two levels up: <project>/data/sample_invoices
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "sample_invoices"        # Sets default invoice folder → Uses data/sample_invoices/ if no path is provided.

# Small status -> symbol map for a readable report.
_STATUS_MARK = {                                                                            # Defines status symbols → Maps invoice statuses like PAID, REVIEW, REJECT.
    InvoiceStatus.PAID: "PAID   ",
    InvoiceStatus.NEEDS_REVIEW: "REVIEW ",
    InvoiceStatus.REJECTED: "REJECT ",
    InvoiceStatus.FAILED: "FAILED ",
}


def _print_record(record: ProcessedInvoice) -> None:                                        # Prints invoice details, risk score, and audit trail.
    """Pretty-print a single processed invoice and its audit trail."""
    inv = record.invoice
    mark = _STATUS_MARK.get(record.status, record.status.value)
    score = record.assessment.risk_score if record.assessment else "?"
    print(f"[{mark}] {inv.invoice_id}  {inv.vendor_name:<22} "
          f"{inv.amount:>12,.2f} {inv.currency}  risk={score}")
    for step in record.audit_trail:
        print(f"         - {step}")
    print()


def main(argv: list[str] | None = None) -> int:                                             # Entry point of the application.
    # Force UTF-8 output so unicode (e.g. em-dashes) renders on Windows consoles.
    try:    
        sys.stdout.reconfigure(encoding="utf-8")                                            # Sets UTF-8 output, Ensures special characters display correctly.
    except (AttributeError, ValueError):
        pass

    argv = argv if argv is not None else sys.argv[1:]                                       # Reads command-line argument → Gets invoice directory from user or uses default.
    data_dir = Path(argv[0]) if argv else _DEFAULT_DATA_DIR

    if not data_dir.exists():                                                               # Checks folder exists → Exits if invoice directory is missing.
        print(f"No invoice directory found at: {data_dir}", file=sys.stderr)
        return 1

    # Report which scoring path will be used, so the run is self-explanatory.
    mode = (                                                                                # Displays scoring mode → Shows whether using LLM or heuristic rules.
        f"LLM via LiteLLM ({settings.llm_provider})"
        if settings.has_llm_credentials
        else "heuristic (LLM disabled)" if settings.disable_llm
        else f"heuristic (no {settings.llm_provider} key set)"
    )
    print(f"Custodian — accounts-payable pipeline")
    print(f"Scoring mode: {mode} | model: {settings.llm_model}")
    print(f"Ledger starting balance: ₹{settings.ledger_balance:,.2f}\n")

    invoices = IngestAgent().from_directory(data_dir)                                       # Loads invoices → IngestAgent().from_directory() reads JSON invoices.
    if not invoices:                                                                            # Validates invoices exist → Exits if no invoice files found.
        print(f"No *.json invoices found in {data_dir}", file=sys.stderr)                           
        return 1

    audit_log = AuditLog(settings.audit_log_path) if settings.audit_log_path else None      # Creates audit log → Initializes audit logging if configured.
    if audit_log:
        print(f"Audit log: {audit_log.path}")
    custodian = Custodian(audit_log=audit_log)                                              # Creates Custodian orchestrator → Main workflow controller.
    records = custodian.process_many(invoices)                                                  # Processes invoices → custodian.process_many(invoices) runs the pipeline.
    for record in records:
        _print_record(record)                                                                   # Prints each result → Shows status, amount, risk, and audit steps.

    # Summary                                                                               # Calculates summary → Counts paid, review, and rejected invoices.
    paid = sum(1 for r in records if r.status is InvoiceStatus.PAID)                        # Calculates total paid amount → Sums all auto-approved invoices.
    review = sum(1 for r in records if r.status is InvoiceStatus.NEEDS_REVIEW)
    rejected = sum(1 for r in records if r.status is InvoiceStatus.REJECTED)
    total_paid = sum(r.invoice.amount for r in records if r.status is InvoiceStatus.PAID)

    print("=" * 60)
    print(f"Processed {len(records)} invoice(s): "                                              
          f"{paid} paid, {review} to review, {rejected} rejected.")
    print(f"Total auto-paid: ₹{total_paid:,.2f}")
    print(f"Ledger balance now: ₹{custodian.ledger.balance:,.2f}")                          # Prints final report → Shows processing statistics and remaining ledger balance.
    return 0                                                                                # Returns 0 → Indicates successful execution.


if __name__ == "__main__":                                                                  # if __name__ == "__main__": → Runs main() when executed directly.
    raise SystemExit(main())


"""
# Custodian Invoice Processing Flow

```text
Start
  │
  ▼
Read CLI Args
  │
  ▼
Locate Invoice Directory
  │
  ▼
Load JSON Invoices
  │
  ▼
Create Audit Log
  │
  ▼
Initialize Custodian
  │
  ▼
Process Invoices
  │
  ├──► Risk Assessment (LLM / Heuristic)
  │
  ├──► Validation Checks
  │
  ├──► Approval Decision
  │         │
  │         ├──► PAID
  │         ├──► NEEDS REVIEW
  │         └──► REJECTED
  │
  └──► Update Audit Trail
  │
  ▼
Print Invoice Results
  │
  ▼
Generate Summary
  │
  ▼
Show Ledger Balance
  │
  ▼
End
```
"""


"""
```text
Invoices (.json)            
      │
      ▼
 IngestAgent                        raw data -> validated invoice model 
      │
      ▼
  Custodian
      │
      ▼
Risk Assessment
(LLM/Heuristic)
      │
      ▼
Decision
 ├─ PAID
 ├─ REVIEW
 └─ REJECT
      │
      ▼
 Audit Log
      │
      ▼
 Report + Summary
```
"""