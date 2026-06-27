"""In-process pub/sub for SSE realtime events.

MVP: single-process, in-memory. Replace with Redis pub/sub or a message
queue when the server scales beyond one process.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Set


class Broker:
    def __init__(self) -> None:
        self._subs: Dict[str, Set["asyncio.Queue[dict]"]] = {}

    def subscribe(self, user_id: str) -> "asyncio.Queue[dict]":
        q: "asyncio.Queue[dict]" = asyncio.Queue()
        self._subs.setdefault(user_id, set()).add(q)
        return q

    def unsubscribe(self, user_id: str, q: "asyncio.Queue[dict]") -> None:
        subs = self._subs.get(user_id)
        if subs:
            subs.discard(q)
            if not subs:
                self._subs.pop(user_id, None)

    def publish(self, user_id: str, event: str, data: Dict[str, Any]) -> None:
        """Fan out an event to all of a user's subscribers (non-blocking)."""
        for q in list(self._subs.get(user_id, ())):
            q.put_nowait({"event": event, "data": data})


broker = Broker()
