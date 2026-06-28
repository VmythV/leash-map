"""Tiny in-process counters exposed at /metrics.

MVP observability without a Prometheus dependency; swap for a real metrics
backend later. Not durable — resets on restart.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict


class Metrics:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = defaultdict(int)

    def inc(self, name: str, n: int = 1) -> None:
        self._counters[name] += n

    def snapshot(self) -> Dict[str, int]:
        return dict(self._counters)


metrics = Metrics()
