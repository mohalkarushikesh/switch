"""Operations/audit layer: append-only log of every processed invoice.

Writes one JSON object per invoice to a JSONL file so decisions are durable and
replayable after the fact — the core auditability promise of the platform.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import ProcessedInvoice


class AuditLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        # Ensure the parent directory exists so the first write can't fail.
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, processed: ProcessedInvoice) -> None:
        """Append one processed invoice as a JSON line."""
        # mode="json" serializes dates and enums to JSON-safe primitives.
        line = json.dumps(processed.model_dump(mode="json"), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def read_all(self) -> list[dict]:
        """Read back every recorded entry (used for verification / replay)."""
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
