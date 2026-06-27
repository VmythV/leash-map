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

    # Placeholder for the future PostgreSQL/PostGIS backend. The MVP uses an
    # in-memory store, so this is currently unused.
    database_url: Optional[str] = None

    # If set, device uploads must present this exact bearer token. If unset,
    # any non-empty device token is accepted (local development only).
    device_token: Optional[str] = None

    # Geofence / alert tuning. See docs/api/realtime-events.md.
    geofence_accuracy_threshold_m: float = 50.0
    geofence_exit_consecutive: int = 2
    low_battery_threshold: int = 15


settings = Settings()
