"""Replacing a device is explicit under the multi-device model: unbind + bind."""
from __future__ import annotations

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def test_explicit_replace():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]

    c.post("/v1/devices/bind", json={"device_id": "dev_a", "pet_id": pet_id}, headers=h)
    # to replace, unbind the old device then bind the new one
    c.delete(f"/v1/pets/{pet_id}/devices/dev_a", headers=h)
    c.post("/v1/devices/bind", json={"device_id": "dev_b", "pet_id": pet_id}, headers=h)

    assert store.pet_for_device("dev_a") is None
    assert store.pet_for_device("dev_b") == pet_id
    ids = {d for d, _ in store.devices_for_pet(pet_id)}
    assert ids == {"dev_b"}
