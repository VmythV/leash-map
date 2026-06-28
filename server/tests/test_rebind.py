"""Clean single-device rebind: the old device is fully detached."""
from __future__ import annotations

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def test_rebind_detaches_old_device():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]

    c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet_id}, headers=h)
    assert store.pet_for_device("dev_a") == pet_id

    # rebind to a new device
    c.post("/v1/devices/bind", json={"device_id": "dev_b", "pet_id": pet_id}, headers=h)
    # old device is no longer attached to the pet (no stale binding)
    assert store.pet_for_device("dev_a") is None
    assert store.pet_for_device("dev_b") == pet_id
    assert store.get_pet(pet_id).device_id == "dev_b"
