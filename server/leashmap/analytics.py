"""Activity / movement analytics — the product's trail-data differentiation.

Pure functions over a time-ordered sequence of samples (anything with
lat/lng/ts/motion_state/speed_mps attributes, e.g. store.LocationRecord).
Computes distance, active time, hourly distribution, and stay/frequent areas
(stop-point clustering). See docs/technical-plan.md §6.4.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Sequence

from .geo import haversine_m

WALK_THRESHOLD_MPS = 0.3


def total_distance_m(pts: Sequence) -> float:
    d = 0.0
    for a, b in zip(pts, pts[1:]):
        d += haversine_m(a.lat, a.lng, b.lat, b.lng)
    return d


def active_seconds(pts: Sequence, walk_threshold_mps: float = WALK_THRESHOLD_MPS) -> int:
    """Sum the durations of segments that imply real movement."""
    total = 0
    for a, b in zip(pts, pts[1:]):
        dt = b.ts - a.ts
        if dt <= 0:
            continue
        speed = haversine_m(a.lat, a.lng, b.lat, b.lng) / dt
        if speed >= walk_threshold_mps:
            total += dt
    return total


def distance_by_hour(pts: Sequence) -> List[float]:
    """Meters travelled bucketed by UTC hour (0..23)."""
    hours = [0.0] * 24
    for a, b in zip(pts, pts[1:]):
        h = datetime.fromtimestamp(a.ts, tz=timezone.utc).hour
        hours[h] += haversine_m(a.lat, a.lng, b.lat, b.lng)
    return [round(x, 1) for x in hours]


def stop_points(pts: Sequence, radius_m: float = 30.0, min_seconds: int = 120) -> List[dict]:
    """Cluster consecutive samples that stay within `radius_m` into stays."""
    stops: List[dict] = []
    n = len(pts)
    i = 0
    while i < n:
        sum_lat, sum_lng, count = pts[i].lat, pts[i].lng, 1
        start_ts = last_ts = pts[i].ts
        j = i + 1
        while j < n:
            clat, clng = sum_lat / count, sum_lng / count
            if haversine_m(pts[j].lat, pts[j].lng, clat, clng) <= radius_m:
                sum_lat += pts[j].lat
                sum_lng += pts[j].lng
                count += 1
                last_ts = pts[j].ts
                j += 1
            else:
                break
        duration = last_ts - start_ts
        if count >= 2 and duration >= min_seconds:
            stops.append({
                "lat": round(sum_lat / count, 6),
                "lng": round(sum_lng / count, 6),
                "count": count,
                "duration_s": duration,
            })
        i = j if j > i else i + 1
    stops.sort(key=lambda s: s["duration_s"], reverse=True)
    return stops


def activity_summary(pts: Sequence, *, stop_radius_m: float = 30.0,
                     min_stop_seconds: int = 120) -> dict:
    moving = sum(1 for p in pts if (p.motion_state == "moving") or ((p.speed_mps or 0) >= WALK_THRESHOLD_MPS))
    active = active_seconds(pts)
    return {
        "point_count": len(pts),
        "distance_m": round(total_distance_m(pts), 1),
        "moving_points": moving,
        "active_minutes": round(active / 60.0, 1),
        "by_hour_m": distance_by_hour(pts),
        "stops": stop_points(pts, stop_radius_m, min_stop_seconds),
    }
