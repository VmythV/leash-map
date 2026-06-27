"""Test config: use an isolated in-memory SQLite database.

Must run before any `leashmap` import so the settings singleton picks it up.
"""
import os

os.environ.setdefault("LEASHMAP_DATABASE_URL", "sqlite://")
os.environ.setdefault("LEASHMAP_DEVICE_TOKEN", "dev-token")
