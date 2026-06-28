"""Per-pet alert toggles, enter/home alert, geofence flags, quiet hours."""
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


def _setup(geofence=None):
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)
    if geofence is not None:
        c.post(f"/v1/pets/{pet_id}/geofences", json=geofence, headers=h)
    return c, h, pet_id


def _open_alerts(c, h, type_):
    return [a for a in c.get("/v1/alerts", params={"status": "open"}, headers=h).json()["data"]
            if a["type"] == type_]


def test_defaults():
    c, h, pet_id = _setup()
    s = c.get(f"/v1/pets/{pet_id}/alert-settings", headers=h).json()
    assert s["exit_enabled"] and s["low_battery_enabled"] and s["offline_enabled"]
    assert s["enter_enabled"] is False


def test_exit_toggle_off_suppresses_alert():
    gf = {"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100}
    c, h, pet_id = _setup(gf)
    c.put(f"/v1/pets/{pet_id}/alert-settings", json={"exit_enabled": False}, headers=h)
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now, 31.2304, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(2, now + 60, 31.2316, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(3, now + 120, 31.2318, 121.4737), headers=_dev())
    assert _open_alerts(c, h, "exit_zone") == []


def test_enter_alert_when_enabled():
    gf = {"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100,
          "alert_on_enter": True}
    c, h, pet_id = _setup(gf)
    c.put(f"/v1/pets/{pet_id}/alert-settings", json={"enter_enabled": True}, headers=h)
    now = int(time.time())
    # start outside, then come home
    c.post("/v1/device/locations", json=_loc(1, now, 31.2330, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(2, now + 60, 31.2304, 121.4737), headers=_dev())
    enters = [a for a in c.get("/v1/alerts", headers=h).json()["data"] if a["type"] == "enter_zone"]
    assert len(enters) == 1


def test_geofence_patch_toggle():
    gf = {"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100}
    c, h, pet_id = _setup(gf)
    geo_id = c.get(f"/v1/pets/{pet_id}/geofences", headers=h).json()["data"][0]["id"]
    r = c.patch(f"/v1/pets/{pet_id}/geofences/{geo_id}", json={"alert_on_enter": True}, headers=h).json()
    assert r["alert_on_enter"] is True


def test_quiet_hours_suppress_delivery_but_keep_alert():
    from datetime import datetime, timezone
    gf = {"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100}
    c, h, pet_id = _setup(gf)
    # quiet window covering the current UTC hour -> delivery suppressed
    hour = datetime.now(timezone.utc).hour
    c.put(f"/v1/pets/{pet_id}/alert-settings",
          json={"quiet_start": hour, "quiet_end": (hour + 1) % 24}, headers=h)
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now, 31.2304, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(2, now + 60, 31.2316, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(3, now + 120, 31.2318, 121.4737), headers=_dev())
    exits = _open_alerts(c, h, "exit_zone")
    assert len(exits) == 1  # alert still created (visible in-app)
    deliveries = store.deliveries_for_alert(exits[0]["id"])
    assert deliveries and all(d["status"] == "suppressed" for d in deliveries)
