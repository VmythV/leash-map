"""Activity analytics: distance, active time, hourly, stop-point clustering."""
from __future__ import annotations

import time
from collections import namedtuple

from fastapi.testclient import TestClient

from leashmap.analytics import (
    active_seconds,
    activity_summary,
    distance_by_hour,
    stop_points,
    total_distance_m,
)
from leashmap.main import create_app
from leashmap.store import store

S = namedtuple("S", "lat lng ts motion_state speed_mps")


def _moving(n, start_ts=0, step_deg=0.0001, step_s=10):
    # ~11m per step every 10s -> ~1.1 m/s
    return [S(31.0 + i * step_deg, 121.0, start_ts + i * step_s, "moving", 1.1) for i in range(n)]


def _stay(n, start_ts=0, step_s=60):
    return [S(31.0, 121.0, start_ts + i * step_s, "still", 0.0) for i in range(n)]


def test_total_distance():
    d = total_distance_m([S(31.0, 121.0, 0, "moving", 0), S(32.0, 121.0, 60, "moving", 0)])
    assert 110_000 < d < 112_000


def test_active_seconds_counts_moving_only():
    assert active_seconds(_moving(5)) > 0
    assert active_seconds(_stay(5)) == 0


def test_stop_points_detects_stay():
    stops = stop_points(_stay(5, step_s=60), radius_m=30, min_seconds=120)
    assert len(stops) == 1
    assert stops[0]["count"] == 5
    assert stops[0]["duration_s"] == 240


def test_stop_points_ignores_short_pass():
    # moving straight through, never stays -> no stops
    assert stop_points(_moving(6, step_deg=0.001), radius_m=30, min_seconds=120) == []


def test_distance_by_hour_sums_to_total():
    pts = _moving(6)
    by_hour = distance_by_hour(pts)
    assert len(by_hour) == 24
    assert abs(sum(by_hour) - total_distance_m(pts)) < 1.0


def test_summary_shape():
    s = activity_summary(_moving(5) + _stay(4, start_ts=1000))
    assert s["point_count"] == 9
    assert s["distance_m"] > 0
    assert s["active_minutes"] > 0
    assert len(s["by_hour_m"]) == 24
    assert len(s["stops"]) >= 1


def test_activity_endpoint():
    store.reset()
    c = TestClient(create_app())
    token = c.post("/v1/auth/demo-session", json={}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    pet_id = c.post("/v1/pets", json={"name": "Buddy"}, headers=h).json()["id"]
    c.post("/v1/devices/bind", json={"device_id": "dev_mvp_001", "pet_id": pet_id}, headers=h)
    now = int(time.time())
    for i in range(4):
        c.post("/v1/device/locations", json={
            "type": "location", "protocol_version": 1, "device_id": "dev_mvp_001",
            "seq": i + 1, "ts": now + i * 30, "lat": 31.2304 + i * 0.0003, "lng": 121.4737,
            "accuracy_m": 8, "source": "simulator", "motion_state": "moving",
        }, headers={"Authorization": "Bearer dev-token"})
    r = c.get(f"/v1/pets/{pet_id}/activity",
              params={"from": "2026-01-01T00:00:00Z", "to": "2030-01-01T00:00:00Z"},
              headers=h).json()
    assert r["point_count"] == 4
    assert r["distance_m"] > 0
    assert len(r["by_hour_m"]) == 24
