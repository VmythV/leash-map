"""Runtime configuration loaded from environment (prefix LEASHMAP_)."""
from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LEASHMAP_",
        env_file=".env",
        extra="ignore",
    )

    app_env: str = "local"

    # MVP persistence is SQLite via SQLAlchemy. Swap this URL for a PostgreSQL
    # DSN later — the ORM layer stays the same (geo math is done in Python, so
    # PostGIS is not required yet).
    database_url: str = "sqlite:///leashmap.db"

    # If set, device uploads must present this exact bearer token. If unset,
    # any non-empty device token is accepted (local development only).
    device_token: Optional[str] = None

    # Geofence / alert tuning. See docs/api/realtime-events.md.
    geofence_accuracy_threshold_m: float = 50.0
    geofence_exit_consecutive: int = 2
    low_battery_threshold: int = 15

    # Offline detection. A bound device with no heartbeat/location within the
    # threshold raises an offline alert. The background scan runs on an interval.
    offline_threshold_seconds: int = 900
    offline_scan_interval_seconds: int = 30

    # Trail simplification (Douglas-Peucker) applied when ?downsample=true.
    trail_downsample_epsilon_m: float = 8.0

    # Ingest quality filters. A point is rejected (not stored) when its
    # timestamp drifts too far from now, or it implies an impossible speed
    # relative to the previous point.
    max_ts_drift_seconds: int = 2_592_000  # 30 days
    max_speed_mps: float = 60.0  # ~216 km/h — far above any pet


settings = Settings()
