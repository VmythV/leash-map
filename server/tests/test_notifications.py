"""Notification dispatch records a delivery status per channel."""
from __future__ import annotations

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _device_headers():
    return {"Authorization": "Bearer dev-token"}


def test_alert_records_console_delivery():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)

    # low battery -> alert -> dispatched to console provider
    c.post("/v1/device/locations", json={
        "type": "location", "protocol_version": 1, "device_id": "dev_mvp_001",
        "seq": 1, "ts": 1782432000, "lat": 31.23, "lng": 121.47,
        "accuracy_m": 8, "source": "simulator", "battery_pct": 5,
    }, headers=_device_headers())

    alerts = c.get("/v1/alerts", headers=h).json()["data"]
    low = [a for a in alerts if a["type"] == "low_battery"]
    assert len(low) == 1

    deliveries = store.deliveries_for_alert(low[0]["id"])
    assert len(deliveries) == 1
    assert deliveries[0]["channel"] == "console"
    assert deliveries[0]["status"] == "sent"
