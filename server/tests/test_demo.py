"""Local web-demo endpoints + SSE token-in-query auth."""
from __future__ import annotations

from fastapi.testclient import TestClient

from leashmap.main import create_app
from leashmap.store import store


def _client() -> TestClient:
    store.reset()
    return TestClient(create_app())


def test_seed_returns_setup():
    c = _client()
    r = c.post("/demo/seed").json()
    assert r["pet_id"].startswith("pet_")
    assert r["device_id"].startswith("dev_demo_")
    assert r["geofence"]["radius_m"] > 0
    assert r["token"].startswith("sess_")


def test_sse_rejects_bad_query_token():
    c = _client()
    r = c.get("/v1/realtime/stream", params={"access_token": "nope"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthenticated"
