"""Notification channel abstraction.

Alerts are pushed to the App over SSE in real time; this layer adds pluggable
out-of-band channels (push / SMS / email later) and records a delivery status
per channel. MVP ships a console placeholder provider for local development.
"""
from __future__ import annotations

import logging
from typing import List, Protocol

from .store import AlertRecord, Store

log = logging.getLogger("leashmap.notifications")


class NotificationProvider(Protocol):
    name: str

    def send(self, alert: AlertRecord) -> bool:
        """Deliver an alert. Return True on success."""
        ...


class ConsoleProvider:
    """Local-dev placeholder: logs the alert instead of sending a real push."""

    name = "console"

    def send(self, alert: AlertRecord) -> bool:
        log.info("[notify] %s/%s -> user %s: %s",
                 alert.type, alert.severity, alert.user_id, alert.message)
        return True


class NotificationService:
    def __init__(self, providers: List[NotificationProvider] | None = None) -> None:
        self.providers: List[NotificationProvider] = providers or [ConsoleProvider()]

    def dispatch(self, store: Store, alert: AlertRecord) -> None:
        for p in self.providers:
            try:
                ok = p.send(alert)
            except Exception:  # a channel failure must not break alerting
                ok = False
            store.record_delivery(alert.id, alert.user_id, p.name, "sent" if ok else "failed")


notifier = NotificationService()
