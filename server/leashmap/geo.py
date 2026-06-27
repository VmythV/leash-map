"""Geospatial helpers. Replaced by PostGIS in the persistent backend."""
from __future__ import annotations

import math

_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two WGS84 points, in meters."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _local_xy(lat: float, lng: float, lat0: float) -> tuple[float, float]:
    """Equirectangular projection to local meters (good enough at trail scale)."""
    x = math.radians(lng) * math.cos(math.radians(lat0)) * _EARTH_RADIUS_M
    y = math.radians(lat) * _EARTH_RADIUS_M
    return x, y


def _perp_distance_m(p, a, b, lat0: float) -> float:
    """Perpendicular distance (m) of point p from segment a-b, via local XY."""
    px, py = _local_xy(p[0], p[1], lat0)
    ax, ay = _local_xy(a[0], a[1], lat0)
    bx, by = _local_xy(b[0], b[1], lat0)
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / seg2
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def douglas_peucker(points: list, epsilon_m: float) -> list:
    """Simplify a polyline (list of (lat, lng)) keeping points that deviate more
    than epsilon_m. Endpoints are always kept. Returns a list of indices to keep.
    """
    n = len(points)
    if n <= 2:
        return list(range(n))
    lat0 = points[0][0]
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        start, end = stack.pop()
        dmax, idx = 0.0, -1
        for i in range(start + 1, end):
            d = _perp_distance_m(points[i], points[start], points[end], lat0)
            if d > dmax:
                dmax, idx = d, i
        if dmax > epsilon_m and idx != -1:
            keep[idx] = True
            stack.append((start, idx))
            stack.append((idx, end))
    return [i for i in range(n) if keep[i]]
