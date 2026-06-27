"""Test config: use an isolated in-memory SQLite database.

Must run before any `leashmap` import so the settings singleton picks it up.
"""
import os

os.environ.setdefault("LEASHMAP_DATABASE_URL", "sqlite://")
os.environ.setdefault("LEASHMAP_DEVICE_TOKEN", "dev-token")
# Keep the background offline scan from firing during tests; we call
# scan_offline() directly with a controlled `now` instead.
os.environ.setdefault("LEASHMAP_OFFLINE_SCAN_INTERVAL_SECONDS", "3600")
