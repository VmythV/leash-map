"""End-to-end smoke test of the MVP loop over the in-memory store.

bind -> ingest inside zone -> ingest outside zone (debounced) -> exit_zone alert
-> latest location -> trail -> low-battery alert -> ack.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _client() -> TestClient:
    store.reset()
    return TestClient(create_app())


def _device_headers():
    return {"Authorization": "Bearer dev-token"}


def _loc(device_id, seq, ts, lat, lng, *, acc=8.0, battery=80):
    return {
        "type": "location",
        "protocol_version": 1,
        "device_id": device_id,
        "seq": seq,
        "ts": ts,
        "lat": lat,
        "lng": lng,
        "accuracy_m": acc,
        "source": "simulator",
        "battery_pct": battery,
        "motion_state": "moving",
    }


def test_health():
    c = _client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auth_required():
    c = _client()
    assert c.get("/v1/pets").status_code == 401


def test_full_loop():
    c = _client()
    # session
    token = c.post("/v1/auth/demo-session", json={"display_name": "May"}).json()["token"]
    app_h = {"Authorization": f"Bearer {token}"}

    # pet + bind
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=app_h).json()["id"]
    dev = "dev_mvp_001"
    r = c.post("/v1/devices/bind", json={"device_id": dev, "pet_id": pet_id}, headers=app_h)
    assert r.status_code == 200

    # safe zone centered at home
    gf = c.post(
        f"/v1/pets/{pet_id}/geofences",
        json={"name": "家", "center_lat": 31.2304, "center_lng": 121.4737, "radius_m": 100},
        headers=app_h,
    )
    assert gf.status_code == 201

    # point inside the zone
    assert c.post("/v1/device/locations", json=_loc(dev, 1, 1782432000, 31.2304, 121.4737),
                  headers=_device_headers()).json()["accepted"] == 1

    # duplicate seq ignored
    dup = c.post("/v1/device/locations", json=_loc(dev, 1, 1782432000, 31.2304, 121.4737),
                 headers=_device_headers()).json()
    assert dup["accepted"] == 0 and dup["duplicated"] == 1

    # two consecutive points well outside -> exit_zone alert (debounced)
    c.post("/v1/device/locations", json=_loc(dev, 2, 1782432060, 31.2400, 121.4737),
           headers=_device_headers())
    c.post("/v1/device/locations", json=_loc(dev, 3, 1782432120, 31.2410, 121.4737),
           headers=_device_headers())

    alerts = c.get("/v1/alerts", headers=app_h).json()["data"]
    exit_alerts = [a for a in alerts if a["type"] == "exit_zone"]
    assert len(exit_alerts) == 1
    assert exit_alerts[0]["status"] == "open"

    # latest location reflects last point
    latest = c.get(f"/v1/pets/{pet_id}/location/latest", headers=app_h).json()
    assert latest["location"]["lat"] == 31.2410
    assert latest["device"]["online"] is True

    # trail returns all 3 unique points
    trail = c.get(
        f"/v1/pets/{pet_id}/trail",
        params={"from": "2026-06-26T00:00:00Z", "to": "2026-06-28T00:00:00Z"},
        headers=app_h,
    ).json()
    assert trail["point_count"] == 3
    assert trail["distance_m"] > 0

    # low battery alert
    c.post("/v1/device/locations", json=_loc(dev, 4, 1782432180, 31.2410, 121.4737, battery=10),
           headers=_device_headers())
    alerts = c.get("/v1/alerts", headers=app_h).json()["data"]
    low = [a for a in alerts if a["type"] == "low_battery"]
    assert len(low) == 1

    # ack the exit alert
    ack = c.post(f"/v1/alerts/{exit_alerts[0]['id']}/ack", headers=app_h).json()
    assert ack["status"] == "acknowledged"
