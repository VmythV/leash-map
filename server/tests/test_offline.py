"""Offline-alert background scan: raise when stale, resolve when back."""
from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from leashmap.broker import broker
from leashmap.main import create_app
from leashmap.services import scan_offline
from leashmap.store import store, utcnow


def _setup() -> TestClient:
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)
    # heartbeat creates device_status with last_seen = now
    c.post("/v1/device/heartbeat", json={
        "type": "heartbeat", "protocol_version": 1, "device_id": "dev_mvp_001",
        "ts": 1782432000, "battery_pct": 80, "mode": "tracking",
    }, headers={"Authorization": "Bearer dev-token"})
    c.app_token = h  # type: ignore[attr-defined]
    return c


def test_offline_raised_then_resolved():
    c = _setup()
    h = c.app_token  # type: ignore[attr-defined]

    # nothing stale yet
    assert scan_offline(store, broker, now=utcnow()) == 0

    # jump past the threshold -> one offline alert
    future = utcnow() + timedelta(hours=1)
    assert scan_offline(store, broker, now=future) == 1
    # idempotent while open
    assert scan_offline(store, broker, now=future) == 0

    open_alerts = c.get("/v1/alerts", params={"status": "open"}, headers=h).json()["data"]
    assert any(a["type"] == "offline" for a in open_alerts)

    # device checks in again, then a scan within threshold resolves it
    c.post("/v1/device/heartbeat", json={
        "type": "heartbeat", "protocol_version": 1, "device_id": "dev_mvp_001",
        "ts": 1782433000, "battery_pct": 79, "mode": "tracking",
    }, headers={"Authorization": "Bearer dev-token"})
    scan_offline(store, broker, now=utcnow())
    open_offline = [a for a in c.get("/v1/alerts", params={"status": "open"}, headers=h).json()["data"]
                    if a["type"] == "offline"]
    assert not open_offline
