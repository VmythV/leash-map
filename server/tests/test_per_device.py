"""Per-device low-battery/offline alerts and device naming."""
from __future__ import annotations

import time
from datetime import timedelta

from fastapi.testclient import TestClient

from leashmap.broker import broker
from leashmap.main import create_app
from leashmap.services import scan_offline
from leashmap.store import store, utcnow


def _dev():
    return {"Authorization": "Bearer dev-token"}


def _loc(device_id, seq, ts, battery=80):
    return {
        "type": "location", "protocol_version": 1, "device_id": device_id,
        "seq": seq, "ts": ts, "lat": 31.2304, "lng": 121.4737, "accuracy_m": 8.0,
        "source": "simulator", "battery_pct": battery, "motion_state": "moving",
    }


def _setup():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet_id}, headers=h)
    c.post("/v1/devices/bind", json={"device_id": "dev_b", "pet_id": pet_id}, headers=h)
    return c, h, pet_id


def test_low_battery_per_device():
    c, h, pet_id = _setup()
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc("dev_a", 1, now, battery=5), headers=_dev())
    c.post("/v1/device/locations", json=_loc("dev_b", 1, now, battery=5), headers=_dev())
    low = [a for a in c.get("/v1/alerts", headers=h).json()["data"] if a["type"] == "low_battery"]
    assert len(low) == 2  # one per device
    assert {a["device_id"] for a in low} == {"dev_a", "dev_b"}


def test_offline_per_device():
    c, h, pet_id = _setup()
    # both devices send a heartbeat (creates device_status)
    for d in ("dev_a", "dev_b"):
        c.post("/v1/device/heartbeat", json={
            "type": "heartbeat", "protocol_version": 1, "device_id": d,
            "ts": 1782432000, "battery_pct": 80, "mode": "tracking",
        }, headers=_dev())
    future = utcnow() + timedelta(hours=1)
    assert scan_offline(store, broker, now=future) == 2  # one per device


def test_device_rename_shows_in_list_and_alert():
    c, h, pet_id = _setup()
    c.put("/v1/devices/dev_a/config", json={"name": "项圈"}, headers=h)
    devices = c.get(f"/v1/pets/{pet_id}/devices", headers=h).json()["data"]
    a = next(d for d in devices if d["device_id"] == "dev_a")
    assert a["name"] == "项圈"
    # alert message uses the nickname
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc("dev_a", 1, now, battery=5), headers=_dev())
    low = [a for a in c.get("/v1/alerts", headers=h).json()["data"]
           if a["type"] == "low_battery" and a["device_id"] == "dev_a"]
    assert len(low) == 1 and "项圈" in low[0]["message"]
