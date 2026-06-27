"""Simulation runner: ties config, route, battery and mode to the HTTP client."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from .client import DeviceClient
from .routes import build_points

# mode -> heartbeat mode reported to the cloud
_HB_MODE = {
    "normal": "tracking",
    "lost": "lost",
    "exit_zone": "guard",
    "drift": "tracking",
    "offline": "tracking",
    "low_battery": "low_battery",
}


@dataclass
class RunnerConfig:
    device_id: str
    endpoint: str
    token: str
    mode: str = "normal"
    interval: float = 1.0
    battery: float = 85.0
    count: int = 20
    batch_size: int = 5
    route: Optional[List[dict]] = None


class Runner:
    def __init__(self, cfg: RunnerConfig) -> None:
        self.cfg = cfg
        self._drain = 2.0 if cfg.mode == "low_battery" else 0.5
        # low_battery: ensure we actually cross the threshold during the run
        if cfg.mode == "low_battery" and cfg.battery > 20:
            cfg.battery = 18.0
        # lost: high-frequency reporting
        if cfg.mode == "lost":
            cfg.interval = min(cfg.interval, 1.0)

    def run(self) -> None:
        cfg = self.cfg
        hb_mode = _HB_MODE.get(cfg.mode, "tracking")
        points = build_points(cfg.mode, cfg.route, cfg.count)

        print(f"device={cfg.device_id} mode={cfg.mode} endpoint={cfg.endpoint} "
              f"points={len(points)} interval={cfg.interval}s")

        battery = cfg.battery
        cache: List[dict] = []

        with DeviceClient(cfg.endpoint, cfg.device_id, cfg.token) as client:
            client.post_heartbeat(int(time.time()), int(round(battery)), hb_mode)

            for i, p in enumerate(points, start=1):
                ts = int(time.time())
                payload = {
                    "seq": i,
                    "ts": ts,
                    "lat": round(p["lat"], 6),
                    "lng": round(p["lng"], 6),
                    "accuracy_m": round(p["accuracy_m"], 1),
                    "source": p.get("source", "simulator"),
                    "battery_pct": int(round(battery)),
                    "motion_state": "moving",
                }

                if cfg.mode == "offline":
                    cache.append(payload)
                    print(f"[{i:>2}] cached seq={i} batt={payload['battery_pct']}% "
                          f"({payload['lat']},{payload['lng']})")
                    if len(cache) >= cfg.batch_size:
                        resp = client.post_batch(ts, cache)
                        print(f"     -> batch flush: accepted={resp['accepted']} "
                              f"duplicated={resp['duplicated']}")
                        cache = []
                else:
                    resp = client.post_location(payload)
                    print(f"[{i:>2}] loc seq={i} ({payload['lat']},{payload['lng']}) "
                          f"acc={payload['accuracy_m']}m batt={payload['battery_pct']}% "
                          f"-> accepted={resp['accepted']}")

                battery = max(0.0, battery - self._drain)
                if i % 5 == 0:
                    client.post_heartbeat(ts, int(round(battery)), hb_mode)
                time.sleep(cfg.interval)

            if cache:
                resp = client.post_batch(int(time.time()), cache)
                print(f"     -> final batch flush: accepted={resp['accepted']} "
                      f"duplicated={resp['duplicated']}")
            client.post_heartbeat(int(time.time()), int(round(battery)), hb_mode)

        print(f"done. final battery={int(round(battery))}%")
