"""Operations layer: notifications for invoices that need attention.

Fires when an invoice is rejected or scored high-risk. Notifiers are
best-effort — a delivery failure never breaks the pipeline.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from pydantic import BaseModel


class Notification(BaseModel):
    invoice_id: str
    events: list[str]        # e.g. ["rejected", "high_risk"]
    status: str
    risk_score: int | None
    vendor_name: str
    amount: float
    message: str


class Notifier:
    """Base interface — implementations deliver a Notification somewhere."""

    def send(self, note: Notification) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class LogNotifier(Notifier):
    """Append notifications to a JSONL file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, note: Notification) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(note.model_dump_json() + "\n")


class WebhookNotifier(Notifier):
    """POST the notification as JSON to a URL (best-effort)."""

    def __init__(self, url: str, timeout: float = 5.0) -> None:
        self.url = url
        self.timeout = timeout

    def send(self, note: Notification) -> None:
        req = urllib.request.Request(
            self.url,
            data=note.model_dump_json().encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=self.timeout).close()
        except Exception:
            # Delivery is best-effort; never let it break invoice processing.
            pass


class MultiNotifier(Notifier):
    """Fan a notification out to several notifiers."""

    def __init__(self, notifiers: list[Notifier]) -> None:
        self.notifiers = list(notifiers)

    def send(self, note: Notification) -> None:
        for n in self.notifiers:
            n.send(note)
