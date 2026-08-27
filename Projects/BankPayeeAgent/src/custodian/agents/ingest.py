"""Ingest agent: turn raw invoice data into a validated Invoice model."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from ..models import Invoice


class IngestAgent:
    """Reads invoices from dicts or JSON files and validates their shape.

    In a fuller system this is where OCR / document parsing would live; here we
    accept already-structured invoice records.
    """

    def from_dict(self, raw: dict) -> Invoice:
        """Validate a single raw invoice record into an Invoice."""
        return Invoice(**self._coerce_dates(raw))

    def from_file(self, path: str | Path) -> Invoice:
        """Load and validate one invoice from a JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.from_dict(data)

    def from_directory(self, directory: str | Path) -> list[Invoice]:
        """Load every *.json invoice in a directory, sorted by filename."""
        folder = Path(directory)
        return [self.from_file(p) for p in sorted(folder.glob("*.json"))]

    @staticmethod
    def _coerce_dates(raw: dict) -> dict:
        """Accept ISO date strings for issue_date / due_date."""
        out = dict(raw)
        for key in ("issue_date", "due_date"):
            value = out.get(key)
            if isinstance(value, str):
                out[key] = datetime.strptime(value, "%Y-%m-%d").date()
            elif isinstance(value, date):
                out[key] = value
        return out
