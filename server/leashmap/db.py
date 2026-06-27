"""SQLAlchemy engine + ORM models (SQLite for MVP, PostgreSQL-ready).

Geo math runs in Python (leashmap/geo.py), so no PostGIS is required: pointing
``LEASHMAP_DATABASE_URL`` at PostgreSQL is the only change needed later.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class SessionRow(Base):
    __tablename__ = "sessions"
    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))


class PetRow(Base):
    __tablename__ = "pets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    species: Mapped[str] = mapped_column(String)
    device_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class BindingRow(Base):
    __tablename__ = "device_bindings"
    device_id: Mapped[str] = mapped_column(String, primary_key=True)
    pet_id: Mapped[str] = mapped_column(String, index=True)
    bound_at: Mapped[datetime] = mapped_column(DateTime)


class LocationRow(Base):
    __tablename__ = "location_points"
    __table_args__ = (UniqueConstraint("device_id", "seq", name="uq_device_seq"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String, index=True)
    pet_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    seq: Mapped[int] = mapped_column()
    ts: Mapped[int] = mapped_column()
    dt: Mapped[datetime] = mapped_column(DateTime, index=True)
    lat: Mapped[float] = mapped_column()
    lng: Mapped[float] = mapped_column()
    accuracy_m: Mapped[float] = mapped_column()
    source: Mapped[str] = mapped_column(String)
    speed_mps: Mapped[Optional[float]] = mapped_column(nullable=True)
    heading: Mapped[Optional[int]] = mapped_column(nullable=True)
    battery_pct: Mapped[Optional[int]] = mapped_column(nullable=True)
    motion_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class GeofenceRow(Base):
    __tablename__ = "geofences"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    pet_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    center_lat: Mapped[float] = mapped_column()
    center_lng: Mapped[float] = mapped_column()
    radius_m: Mapped[float] = mapped_column()
    enabled: Mapped[bool] = mapped_column(default=True)
    # runtime debounce state (kept alongside the fence row for MVP simplicity)
    consecutive_outside: Mapped[int] = mapped_column(default=0)
    open_alert_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class AlertRow(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    pet_id: Mapped[str] = mapped_column(String, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    message: Mapped[str] = mapped_column(String)
    location_point_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class DeviceStatusRow(Base):
    __tablename__ = "device_status"
    device_id: Mapped[str] = mapped_column(String, primary_key=True)
    mode: Mapped[str] = mapped_column(String, default="idle")
    battery_pct: Mapped[Optional[int]] = mapped_column(nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class DeviceEventRow(Base):
    __tablename__ = "device_events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String, index=True)
    ts: Mapped[int] = mapped_column()
    event: Mapped[str] = mapped_column(String)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


def _make_engine(url: str):
    is_sqlite = url.startswith("sqlite")
    kwargs: dict = {}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(engine)
