"""Ingest quality filters, metrics, and geofence re-entry."""
from __future__ import annotations

import time

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _dev():
    return {"Authorization": "Bearer dev-token"}


def _loc(seq, ts, lat, lng, acc=8.0, battery=80):
    return {
        "type": "location", "protocol_version": 1, "device_id": "dev_mvp_001",
        "seq": seq, "ts": ts, "lat": lat, "lng": lng, "accuracy_m": acc,
        "source": "simulator", "battery_pct": battery, "motion_state": "moving",
    }


def _setup():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)
    return c, h, pet_id


def test_rejects_bad_timestamp():
    c, h, _ = _setup()
    r = c.post("/v1/device/locations", json=_loc(1, 0, 31.23, 121.47), headers=_dev()).json()
    assert r["accepted"] == 0 and r["rejected"] == 1


def test_rejects_speed_jump():
    c, h, _ = _setup()
    now = int(time.time())
    # first point accepted
    assert c.post("/v1/device/locations", json=_loc(1, now, 31.2304, 121.4737), headers=_dev()).json()["accepted"] == 1
    # ~100km away 1s later -> impossible speed -> rejected
    r = c.post("/v1/device/locations", json=_loc(2, now + 1, 32.2304, 121.4737), headers=_dev()).json()
    assert r["rejected"] == 1


def test_geofence_reentry_resolves():
    c, h, pet_id = _setup()
    c.post(f"/v1/pets/{pet_id}/geofences",
           json={"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100},
           headers=h)
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now, 31.2304, 121.4737), headers=_dev())
    # leave -> two outside points (close enough in distance to avoid speed reject)
    c.post("/v1/device/locations", json=_loc(2, now + 60, 31.2316, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(3, now + 120, 31.2318, 121.4737), headers=_dev())
    open_now = [a for a in c.get("/v1/alerts", params={"status": "open"}, headers=h).json()["data"] if a["type"] == "exit_zone"]
    assert len(open_now) == 1
    # return inside -> exit alert resolved
    c.post("/v1/device/locations", json=_loc(4, now + 180, 31.2304, 121.4737), headers=_dev())
    open_after = [a for a in c.get("/v1/alerts", params={"status": "open"}, headers=h).json()["data"] if a["type"] == "exit_zone"]
    assert len(open_after) == 0


def test_metrics_endpoint():
    c, h, _ = _setup()
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now, 31.2304, 121.4737), headers=_dev())
    m = c.get("/metrics").json()
    assert m["locations_accepted"] >= 1
    assert "http_requests" in m
    assert "sse_subscribers" in m
