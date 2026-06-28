"""Timezone-localized quiet hours and alert fan-out to shared users."""
from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _dev():
    return {"Authorization": "Bearer dev-token"}


def _loc(seq, ts, lat=31.2304, lng=121.4737):
    return {
        "type": "location", "protocol_version": 1, "device_id": "dev_mvp_001",
        "seq": seq, "ts": ts, "lat": lat, "lng": lng, "accuracy_m": 8.0,
        "source": "simulator", "battery_pct": 80, "motion_state": "moving",
    }


def _setup():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)
    c.post(f"/v1/pets/{pet_id}/geofences",
           json={"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100},
           headers=h)
    return c, h, pet_id


def _trip_exit(c):
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now, 31.2304, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(2, now + 60, 31.2316, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(3, now + 120, 31.2318, 121.4737), headers=_dev())


def test_invalid_timezone_rejected():
    c, h, pet_id = _setup()
    r = c.put(f"/v1/pets/{pet_id}/alert-settings", json={"timezone": "Mars/Olympus"}, headers=h)
    assert r.status_code == 400


def test_quiet_hours_use_local_timezone():
    c, h, pet_id = _setup()
    tz = "Asia/Shanghai"
    local_hour = datetime.now(ZoneInfo(tz)).hour
    # quiet window covering the current *local* hour -> delivery suppressed
    c.put(f"/v1/pets/{pet_id}/alert-settings",
          json={"timezone": tz, "quiet_start": local_hour, "quiet_end": (local_hour + 1) % 24},
          headers=h)
    _trip_exit(c)
    exits = [a for a in c.get("/v1/alerts", headers=h).json()["data"] if a["type"] == "exit_zone"]
    assert len(exits) == 1
    deliveries = store.deliveries_for_alert(exits[0]["id"])
    assert deliveries and all(d["status"] == "suppressed" for d in deliveries)


def test_alert_fans_out_to_shared_user():
    c, h, pet_id = _setup()
    sess2 = c.post("/v1/auth/demo-session", json={"display_name": "Bob"}).json()
    h2 = {"Authorization": f"Bearer {sess2['token']}"}
    user2 = sess2["user"]["id"]
    c.post(f"/v1/pets/{pet_id}/shares", json={"user_id": user2}, headers=h)

    _trip_exit(c)
    # the sharee sees the shared pet's alert
    alerts2 = [a for a in c.get("/v1/alerts", headers=h2).json()["data"] if a["type"] == "exit_zone"]
    assert len(alerts2) == 1
    # and can acknowledge it
    ack = c.post(f"/v1/alerts/{alerts2[0]['id']}/ack", headers=h2)
    assert ack.status_code == 200 and ack.json()["status"] == "acknowledged"


def test_non_shared_user_sees_no_alerts():
    c, h, pet_id = _setup()
    sess2 = c.post("/v1/auth/demo-session", json={}).json()
    h2 = {"Authorization": f"Bearer {sess2['token']}"}
    _trip_exit(c)
    assert c.get("/v1/alerts", headers=h2).json()["data"] == []
