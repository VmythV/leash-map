import random

from leashmap_sim.cli import parse_interval
from leashmap_sim.routes import (
    DEFAULT_ORIGIN,
    apply_drift,
    build_points,
    haversine_m,
    random_walk,
    walk_away,
)


def test_parse_interval():
    assert parse_interval("5s") == 5.0
    assert parse_interval("500ms") == 0.5
    assert parse_interval("2") == 2.0


def test_random_walk_length():
    pts = random_walk(DEFAULT_ORIGIN, 10, rng=random.Random(1))
    assert len(pts) == 10
    assert all(p["source"] == "simulator" for p in pts)


def test_walk_away_increases_distance():
    pts = walk_away(DEFAULT_ORIGIN, 6, step_m=15)
    d_first = haversine_m(*DEFAULT_ORIGIN, pts[0]["lat"], pts[0]["lng"])
    d_last = haversine_m(*DEFAULT_ORIGIN, pts[-1]["lat"], pts[-1]["lng"])
    assert d_last > d_first
    assert d_last > 60  # left a typical safe zone radius


def test_drift_lowers_accuracy():
    base = {"lat": DEFAULT_ORIGIN[0], "lng": DEFAULT_ORIGIN[1], "accuracy_m": 8, "source": "simulator"}
    drifted = apply_drift(base, rng=random.Random(2))
    assert drifted["accuracy_m"] > 50


def test_build_points_count():
    route = [{"lat": 31.23, "lng": 121.47, "accuracy_m": 10, "source": "simulator"}]
    assert len(build_points("normal", route, 7)) == 7
    assert len(build_points("exit_zone", route, 5)) == 5
    assert len(build_points("drift", None, 4)) == 4
