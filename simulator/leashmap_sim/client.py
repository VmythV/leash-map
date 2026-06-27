"""HTTP client for the LeashMap device ingestion API."""
from __future__ import annotations

from typing import List

import httpx

PROTOCOL_VERSION = 1


class DeviceClient:
    def __init__(self, endpoint: str, device_id: str, token: str, timeout: float = 10.0) -> None:
        self.device_id = device_id
        # trust_env=False: ignore ambient HTTP(S)/ALL_PROXY env vars — the device
        # client talks directly to the cloud endpoint.
        self._http = httpx.Client(
            base_url=endpoint.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            trust_env=False,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "DeviceClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def post_location(self, point: dict) -> dict:
        body = {
            "type": "location",
            "protocol_version": PROTOCOL_VERSION,
            "device_id": self.device_id,
            **point,
        }
        r = self._http.post("/v1/device/locations", json=body)
        r.raise_for_status()
        return r.json()

    def post_batch(self, ts: int, points: List[dict]) -> dict:
        body = {
            "type": "location_batch",
            "protocol_version": PROTOCOL_VERSION,
            "device_id": self.device_id,
            "ts": ts,
            "points": points,
        }
        r = self._http.post("/v1/device/locations/batch", json=body)
        r.raise_for_status()
        return r.json()

    def post_heartbeat(self, ts: int, battery_pct: int, mode: str) -> dict:
        body = {
            "type": "heartbeat",
            "protocol_version": PROTOCOL_VERSION,
            "device_id": self.device_id,
            "ts": ts,
            "battery_pct": battery_pct,
            "mode": mode,
            "network": {"type": "simulator", "rssi": -70},
            "firmware_version": "sim-0.1.0",
        }
        r = self._http.post("/v1/device/heartbeat", json=body)
        r.raise_for_status()
        return r.json()
