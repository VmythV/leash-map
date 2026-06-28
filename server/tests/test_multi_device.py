"""One pet, multiple devices."""
from __future__ import annotations

import time

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _loc(device_id, seq, ts, lat, lng):
    return {
        "type": "location", "protocol_version": 1, "device_id": device_id,
        "seq": seq, "ts": ts, "lat": lat, "lng": lng, "accuracy_m": 8.0,
        "source": "simulator", "battery_pct": 80, "motion_state": "moving",
    }


def _setup():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    return c, h, pet_id


def _dev():
    return {"Authorization": "Bearer dev-token"}


def test_pet_holds_multiple_devices():
    c, h, pet_id = _setup()
    c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet_id}, headers=h)
    c.post("/v1/devices/bind", json={"device_id": "dev_b", "pet_id": pet_id}, headers=h)

    devices = c.get(f"/v1/pets/{pet_id}/devices", headers=h).json()["data"]
    ids = {d["device_id"] for d in devices}
    assert ids == {"dev_a", "dev_b"}
    primary = [d for d in devices if d["primary"]]
    assert len(primary) == 1 and primary[0]["device_id"] == "dev_b"  # last bound


def test_points_from_all_devices_attach_to_pet():
    c, h, pet_id = _setup()
    c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet_id}, headers=h)
    c.post("/v1/devices/bind", json={"device_id": "dev_b", "pet_id": pet_id}, headers=h)
    now = int(time.time())
    c.post("/v1/device/locations", json=_loc("dev_a", 1, now, 31.20, 121.40), headers=_dev())
    c.post("/v1/device/locations", json=_loc("dev_b", 1, now + 30, 31.21, 121.41), headers=_dev())
    trail = c.get(f"/v1/pets/{pet_id}/trail",
                  params={"from": "2000-01-01T00:00:00Z", "to": "2100-01-01T00:00:00Z", "downsample": "false"},
                  headers=h).json()
    assert trail["point_count"] == 2


def test_unbind_one_device():
    c, h, pet_id = _setup()
    c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet_id}, headers=h)
    c.post("/v1/devices/bind", json={"device_id": "dev_b", "pet_id": pet_id}, headers=h)
    r = c.delete(f"/v1/pets/{pet_id}/devices/dev_b", headers=h)
    assert r.status_code == 200
    devices = c.get(f"/v1/pets/{pet_id}/devices", headers=h).json()["data"]
    assert {d["device_id"] for d in devices} == {"dev_a"}
    assert store.get_pet(pet_id).device_id == "dev_a"  # primary fell back


def test_device_still_one_pet():
    c, h, pet_id = _setup()
    pet2 = c.post("/v1/pets", json={"name": "Mimi"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet_id}, headers=h)
    r = c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet2}, headers=h)
    assert r.status_code == 409
