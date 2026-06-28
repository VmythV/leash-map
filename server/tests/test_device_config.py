"""Device LED/config + set_config downlink command."""
from __future__ import annotations

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _setup():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)
    return c, h


def _heartbeat(c):
    return c.post("/v1/device/heartbeat", json={
        "type": "heartbeat", "protocol_version": 1, "device_id": "dev_mvp_001",
        "ts": 1782432000, "battery_pct": 80, "mode": "tracking",
    }, headers={"Authorization": "Bearer dev-token"}).json()


def test_defaults():
    c, h = _setup()
    cfg = c.get("/v1/devices/dev_mvp_001/config", headers=h).json()
    assert cfg["led_pattern"] == "blink"
    assert cfg["led_morse"] == "SOS"
    assert cfg["power_mode"] == "normal"


def test_update_pushes_set_config():
    c, h = _setup()
    r = c.put("/v1/devices/dev_mvp_001/config",
              json={"led_pattern": "morse", "led_morse": "HELP", "report_interval_s": 60},
              headers=h).json()
    assert r["led_pattern"] == "morse" and r["led_morse"] == "HELP"

    cmds = _heartbeat(c)["commands"]
    cfg_cmds = [x for x in cmds if x["type"] == "set_config"]
    assert len(cfg_cmds) == 1
    assert cfg_cmds[0]["params"]["led_pattern"] == "morse"
    assert cfg_cmds[0]["params"]["led_morse"] == "HELP"


def test_invalid_pattern_rejected():
    c, h = _setup()
    r = c.put("/v1/devices/dev_mvp_001/config", json={"led_pattern": "rainbow"}, headers=h)
    assert r.status_code == 400


def test_unbound_device_not_found():
    c, h = _setup()
    r = c.get("/v1/devices/dev_unknown/config", headers=h)
    assert r.status_code == 404
