"""SQLite persistence: durable store + append-only audit log.

Replaces the in-memory store and JSONL audit with a single SQLite database so
processed invoices and their audit trail survive restarts. Uses the standard
library ``sqlite3`` (no extra dependency). A single shared connection is
serialized with a lock, which is safe under FastAPI's threadpool.

Set ``CUSTODIAN_DB_PATH`` to a file for durability, or ``:memory:`` (the test
default) for an ephemeral database.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from .models import ProcessedInvoice

_SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_invoices (
    invoice_id  TEXT PRIMARY KEY,
    status      TEXT NOT NULL,
    vendor_name TEXT,
    amount      REAL,
    risk_score  INTEGER,
    payload     TEXT NOT NULL,          -- full ProcessedInvoice as JSON
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  TEXT,
    status      TEXT,
    payload     TEXT NOT NULL,          -- ProcessedInvoice snapshot at record time
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    """Owns the SQLite connection and serializes access with a lock."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # check_same_thread=False: FastAPI runs sync endpoints across threads;
        # the lock below keeps concurrent access serialized and safe.
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self._lock:
            self._conn.execute(sql, params)
            self._conn.commit()

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()


class SqliteStore:
    """Durable replacement for InvoiceStore — one row per invoice (latest state)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, record: ProcessedInvoice) -> None:
        """Insert or update the invoice, preserving its original created_at."""
        inv = record.invoice
        self.db.execute(
            """
            INSERT INTO processed_invoices
                (invoice_id, status, vendor_name, amount, risk_score, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(invoice_id) DO UPDATE SET
                status = excluded.status,
                vendor_name = excluded.vendor_name,
                amount = excluded.amount,
                risk_score = excluded.risk_score,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                inv.invoice_id,
                record.status.value,
                inv.vendor_name,
                inv.amount,
                record.assessment.risk_score if record.assessment else None,
                record.model_dump_json(),
            ),
        )

    def get(self, invoice_id: str) -> ProcessedInvoice | None:
        rows = self.db.query(
            "SELECT payload FROM processed_invoices WHERE invoice_id = ?", (invoice_id,)
        )
        if not rows:
            return None
        return ProcessedInvoice.model_validate_json(rows[0]["payload"])

    def has(self, invoice_id: str) -> bool:
        """True if an invoice with this id has already been processed."""
        return bool(
            self.db.query(
                "SELECT 1 FROM processed_invoices WHERE invoice_id = ? LIMIT 1",
                (invoice_id,),
            )
        )

    def delete(self, invoice_id: str) -> None:
        """Remove a processed invoice (no-op if it doesn't exist)."""
        self.db.execute("DELETE FROM processed_invoices WHERE invoice_id = ?", (invoice_id,))

    def list(self, status: str | None = None) -> list[ProcessedInvoice]:
        # Newest first. rowid is the insertion-order tiebreaker for records that
        # share a (second-resolution) created_at timestamp.
        if status:
            rows = self.db.query(
                "SELECT payload FROM processed_invoices WHERE status = ? "
                "ORDER BY created_at DESC, rowid DESC",
                (status,),
            )
        else:
            rows = self.db.query(
                "SELECT payload FROM processed_invoices ORDER BY created_at DESC, rowid DESC"
            )
        return [ProcessedInvoice.model_validate_json(r["payload"]) for r in rows]


class SqliteAuditLog:
    """Append-only audit log backed by the audit_events table.

    Interface-compatible with governance.AuditLog (record/read_all/path).
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.path = f"sqlite:{db.path}#audit_events"

    def record(self, processed: ProcessedInvoice) -> None:
        self.db.execute(
            "INSERT INTO audit_events (invoice_id, status, payload) VALUES (?, ?, ?)",
            (processed.invoice.invoice_id, processed.status.value, processed.model_dump_json()),
        )

    def read_all(self) -> list[dict]:
        rows = self.db.query("SELECT payload FROM audit_events ORDER BY id")
        return [json.loads(r["payload"]) for r in rows]
