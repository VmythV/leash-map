"""Route loading and generation. Pure functions (no I/O except load_route).

A "point" is a dict: {lat, lng, accuracy_m, source}. See
docs/api/device-protocol.md and docs/detailed-design/device-simulator.md.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import List, Optional

_M_PER_DEG_LAT = 111_320.0
_EARTH_RADIUS_M = 6_371_000.0

# Default origin (a park in Shanghai) used when no route fixture is given.
DEFAULT_ORIGIN = (31.2304, 121.4737)


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


def offset(lat: float, lng: float, north_m: float, east_m: float) -> tuple[float, float]:
    """Offset a point by meters (north, east)."""
    dlat = north_m / _M_PER_DEG_LAT
    dlng = east_m / (_M_PER_DEG_LAT * math.cos(math.radians(lat)))
    return lat + dlat, lng + dlng


def load_route(path: str) -> List[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    points = data["points"]
    if not points:
        raise ValueError("route fixture has no points")
    return points


def random_walk(start: tuple[float, float], n: int, step_m: float = 8.0,
                rng: Optional[random.Random] = None) -> List[dict]:
    rng = rng or random.Random()
    lat, lng = start
    out: List[dict] = []
    for _ in range(n):
        bearing = rng.uniform(0, 2 * math.pi)
        lat, lng = offset(lat, lng, step_m * math.cos(bearing), step_m * math.sin(bearing))
        out.append({"lat": lat, "lng": lng, "accuracy_m": rng.uniform(6, 18), "source": "simulator"})
    return out


def walk_away(start: tuple[float, float], n: int, step_m: float = 15.0,
              bearing_deg: float = 45.0) -> List[dict]:
    """A straight path moving away from `start` — used to leave a safe zone."""
    b = math.radians(bearing_deg)
    out: List[dict] = []
    lat, lng = start
    for _ in range(n):
        lat, lng = offset(lat, lng, step_m * math.cos(b), step_m * math.sin(b))
        out.append({"lat": lat, "lng": lng, "accuracy_m": 10.0, "source": "simulator"})
    return out


def apply_drift(point: dict, rng: Optional[random.Random] = None) -> dict:
    """Inject a low-accuracy, shifted point (bad GNSS fix)."""
    rng = rng or random.Random()
    shift = rng.uniform(30, 80)
    bearing = rng.uniform(0, 2 * math.pi)
    lat, lng = offset(point["lat"], point["lng"], shift * math.cos(bearing), shift * math.sin(bearing))
    return {"lat": lat, "lng": lng, "accuracy_m": rng.uniform(60, 150), "source": "simulator"}


def build_points(mode: str, route: Optional[List[dict]], count: int,
                 rng: Optional[random.Random] = None) -> List[dict]:
    """Produce `count` points for the given mode."""
    rng = rng or random.Random()
    origin = (route[0]["lat"], route[0]["lng"]) if route else DEFAULT_ORIGIN

    if mode == "exit_zone":
        return walk_away(origin, count)

    base = route or random_walk(origin, count, rng=rng)
    points = [dict(base[i % len(base)]) for i in range(count)]

    if mode == "drift":
        points = [apply_drift(p, rng) for p in points]
    return points
