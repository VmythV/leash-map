"""Downlink command queue: enqueue -> delivered on uplink -> acked -> gone."""
from __future__ import annotations

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _device_headers():
    return {"Authorization": "Bearer dev-token"}


def _heartbeat(c, mode="tracking"):
    return c.post("/v1/device/heartbeat", json={
        "type": "heartbeat", "protocol_version": 1, "device_id": "dev_mvp_001",
        "ts": 1782432000, "battery_pct": 80, "mode": mode,
    }, headers=_device_headers()).json()


def test_lost_mode_command_roundtrip():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)

    # no commands initially
    assert _heartbeat(c)["commands"] == []

    # App turns on lost mode -> command enqueued
    r = c.post(f"/v1/pets/{pet_id}/lost-mode", json={"on": True}, headers=h).json()
    cid = r["command"]["command_id"]
    assert r["command"]["type"] == "set_mode"
    assert r["command"]["params"] == {"mode": "lost"}

    # delivered on the next uplink, and keeps being delivered until acked
    cmds = _heartbeat(c)["commands"]
    assert len(cmds) == 1 and cmds[0]["command_id"] == cid
    assert _heartbeat(c)["commands"][0]["command_id"] == cid

    # device acks via a command_ack event
    c.post("/v1/device/events", json={
        "type": "event", "protocol_version": 1, "device_id": "dev_mvp_001",
        "ts": 1782432060, "event": "command_ack",
        "data": {"command_id": cid, "status": "applied"},
    }, headers=_device_headers())

    # no longer delivered
    assert _heartbeat(c)["commands"] == []


def test_lost_mode_requires_bound_device():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    r = c.post(f"/v1/pets/{pet_id}/lost-mode", json={"on": True}, headers=h)
    assert r.status_code == 409
