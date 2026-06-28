"""Batch 3: pause tracking, retention purge, geofence active window, sharing."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store, utcnow


def _dev():
    return {"Authorization": "Bearer dev-token"}


def _loc(seq, ts, lat=31.2304, lng=121.4737, acc=8.0):
    return {
        "type": "location", "protocol_version": 1, "device_id": "dev_mvp_001",
        "seq": seq, "ts": ts, "lat": lat, "lng": lng, "accuracy_m": acc,
        "source": "simulator", "battery_pct": 80, "motion_state": "moving",
    }


def _setup():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)
    return c, h, pet_id, token


def _trail_count(c, h, pet_id):
    r = c.get(f"/v1/pets/{pet_id}/trail",
              params={"from": "2000-01-01T00:00:00Z", "to": "2100-01-01T00:00:00Z", "downsample": "false"},
              headers=h).json()
    return r["point_count"]


def test_pause_drops_points():
    c, h, pet_id, _ = _setup()
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now), headers=_dev())
    c.put(f"/v1/pets/{pet_id}/alert-settings", json={"tracking_paused": True}, headers=h)
    r = c.post("/v1/device/locations", json=_loc(2, now + 10), headers=_dev()).json()
    assert r["accepted"] == 0
    assert _trail_count(c, h, pet_id) == 1  # second point not stored


def test_retention_purge():
    c, h, pet_id, _ = _setup()
    c.put(f"/v1/pets/{pet_id}/alert-settings", json={"retention_days": 1}, headers=h)
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now - 2 * 86400), headers=_dev())  # 2 days old
    c.post("/v1/device/locations", json=_loc(2, now), headers=_dev())
    assert _trail_count(c, h, pet_id) == 2
    deleted = store.purge_expired_locations(utcnow())
    assert deleted == 1
    assert _trail_count(c, h, pet_id) == 1


def test_active_window_suppresses_outside_hours():
    gf_hour = datetime.now(timezone.utc).hour
    inactive_start = (gf_hour + 2) % 24
    inactive_end = (gf_hour + 3) % 24
    c, h, pet_id, _ = _setup()
    c.post(f"/v1/pets/{pet_id}/geofences",
           json={"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100},
           headers=h)
    geo_id = c.get(f"/v1/pets/{pet_id}/geofences", headers=h).json()["data"][0]["id"]
    # window that does NOT include the current hour -> geofence inactive now
    c.patch(f"/v1/pets/{pet_id}/geofences/{geo_id}",
            json={"active_start": inactive_start, "active_end": inactive_end}, headers=h)
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now, 31.2304, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(2, now + 60, 31.2316, 121.4737), headers=_dev())
    c.post("/v1/device/locations", json=_loc(3, now + 120, 31.2318, 121.4737), headers=_dev())
    exits = [a for a in c.get("/v1/alerts", headers=h).json()["data"] if a["type"] == "exit_zone"]
    assert exits == []


def test_sharing_grants_read():
    c, h, pet_id, _ = _setup()
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc(1, now), headers=_dev())
    # a second user
    token2 = c.post("/v1/auth/demo-session", json={"display_name": "Bob"}).json()["token"]
    h2 = {"Authorization": f"Bearer {token2}"}
    uid2 = c.get("/v1/pets", headers=h2)  # ensure session works
    # before share: forbidden
    assert c.get(f"/v1/pets/{pet_id}/location/latest", headers=h2).status_code == 403
    # owner shares with user2 — need user2 id; create a pet for user2 to learn id via share error path
    # fetch user2 id from a fresh session-bound user: use demo-session response
    sess2 = c.post("/v1/auth/demo-session", json={"display_name": "Carol"}).json()
    user2_id = sess2["user"]["id"]
    h3 = {"Authorization": f"Bearer {sess2['token']}"}
    r = c.post(f"/v1/pets/{pet_id}/shares", json={"user_id": user2_id}, headers=h)
    assert r.status_code == 200
    # user3 can now read
    assert c.get(f"/v1/pets/{pet_id}/location/latest", headers=h3).status_code == 200
    # and the shared pet shows up in their list as shared
    pets = c.get("/v1/pets", headers=h3).json()["data"]
    assert any(p["id"] == pet_id and p["shared"] for p in pets)
