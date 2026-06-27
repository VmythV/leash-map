"""Persistence store over SQLAlchemy (SQLite for MVP).

Returns detached DTO dataclasses so the router/service layers never touch ORM
sessions. Each method is a small unit of work that commits on success. Swapping
SQLite for PostgreSQL is a URL change only (see config / db).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select

from . import db
from .db import (
    AlertRow,
    BindingRow,
    DeviceEventRow,
    DeviceStatusRow,
    GeofenceRow,
    LocationRow,
    PetRow,
    SessionRow,
    UserRow,
)
from .ids import gen_id
from .schemas import LocationPoint, User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def to_iso(dt: datetime) -> str:
    return _as_utc(dt).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------- DTOs ----------------
@dataclass
class LocationRecord:
    id: int
    device_id: str
    pet_id: Optional[str]
    seq: int
    ts: int
    dt: datetime
    lat: float
    lng: float
    accuracy_m: float
    source: str
    speed_mps: Optional[float] = None
    heading: Optional[int] = None
    battery_pct: Optional[int] = None
    motion_state: Optional[str] = None


@dataclass
class GeofenceRecord:
    id: str
    pet_id: str
    name: str
    center_lat: float
    center_lng: float
    radius_m: float
    enabled: bool
    consecutive_outside: int = 0
    open_alert_id: Optional[str] = None


@dataclass
class AlertRecord:
    id: str
    user_id: str
    pet_id: str
    device_id: Optional[str]
    type: str
    severity: str
    status: str
    message: str
    location_point_id: Optional[int]
    created_at: datetime
    acknowledged_at: Optional[datetime] = None


@dataclass
class DeviceStatusRecord:
    device_id: str
    mode: str
    battery_pct: Optional[int] = None
    last_seen: Optional[datetime] = None


@dataclass
class PetRecord:
    id: str
    owner_id: str
    name: str
    species: str
    device_id: Optional[str] = None


# ---------------- row -> DTO ----------------
def _loc(r: LocationRow) -> LocationRecord:
    return LocationRecord(
        id=r.id, device_id=r.device_id, pet_id=r.pet_id, seq=r.seq, ts=r.ts,
        dt=_as_utc(r.dt), lat=r.lat, lng=r.lng, accuracy_m=r.accuracy_m, source=r.source,
        speed_mps=r.speed_mps, heading=r.heading, battery_pct=r.battery_pct,
        motion_state=r.motion_state,
    )


def _gf(r: GeofenceRow) -> GeofenceRecord:
    return GeofenceRecord(
        id=r.id, pet_id=r.pet_id, name=r.name, center_lat=r.center_lat,
        center_lng=r.center_lng, radius_m=r.radius_m, enabled=r.enabled,
        consecutive_outside=r.consecutive_outside, open_alert_id=r.open_alert_id,
    )


def _alert(r: AlertRow) -> AlertRecord:
    return AlertRecord(
        id=r.id, user_id=r.user_id, pet_id=r.pet_id, device_id=r.device_id, type=r.type,
        severity=r.severity, status=r.status, message=r.message,
        location_point_id=r.location_point_id, created_at=_as_utc(r.created_at),
        acknowledged_at=_as_utc(r.acknowledged_at),
    )


def _pet(r: PetRow) -> PetRecord:
    return PetRecord(id=r.id, owner_id=r.owner_id, name=r.name, species=r.species, device_id=r.device_id)


def _status(r: DeviceStatusRow) -> DeviceStatusRecord:
    return DeviceStatusRecord(device_id=r.device_id, mode=r.mode, battery_pct=r.battery_pct, last_seen=_as_utc(r.last_seen))


class Store:
    def __init__(self) -> None:
        db.init_db()

    def reset(self) -> None:
        db.Base.metadata.drop_all(db.engine)
        db.Base.metadata.create_all(db.engine)

    # ---- users / sessions ----
    def create_demo_user(self, display_name: Optional[str]) -> Tuple[User, str]:
        user = User(id=gen_id("usr"), display_name=display_name)
        token = "sess_" + gen_id("", 16).lstrip("_")
        with db.SessionLocal() as s:
            s.add(UserRow(id=user.id, display_name=display_name))
            s.add(SessionRow(token=token, user_id=user.id))
            s.commit()
        return user, token

    def user_for_session(self, token: str) -> Optional[User]:
        with db.SessionLocal() as s:
            row = s.get(SessionRow, token)
            if not row:
                return None
            u = s.get(UserRow, row.user_id)
            return User(id=u.id, display_name=u.display_name) if u else None

    # ---- pets / bindings ----
    def create_pet(self, owner_id: str, name: str, species: str) -> PetRecord:
        rec = PetRecord(id=gen_id("pet"), owner_id=owner_id, name=name, species=species)
        with db.SessionLocal() as s:
            s.add(PetRow(id=rec.id, owner_id=owner_id, name=name, species=species, device_id=None))
            s.commit()
        return rec

    def pets_for_owner(self, owner_id: str) -> List[PetRecord]:
        with db.SessionLocal() as s:
            rows = s.scalars(select(PetRow).where(PetRow.owner_id == owner_id)).all()
            return [_pet(r) for r in rows]

    def get_pet(self, pet_id: str) -> Optional[PetRecord]:
        with db.SessionLocal() as s:
            r = s.get(PetRow, pet_id)
            return _pet(r) if r else None

    def pet_for_device(self, device_id: str) -> Optional[str]:
        with db.SessionLocal() as s:
            r = s.get(BindingRow, device_id)
            return r.pet_id if r else None

    def bind(self, device_id: str, pet_id: str) -> datetime:
        bound_at = utcnow()
        with db.SessionLocal() as s:
            prev = s.get(BindingRow, device_id)
            if prev:
                prev_pet = s.get(PetRow, prev.pet_id)
                if prev_pet:
                    prev_pet.device_id = None
                s.delete(prev)
            s.add(BindingRow(device_id=device_id, pet_id=pet_id, bound_at=bound_at))
            pet = s.get(PetRow, pet_id)
            if pet:
                pet.device_id = device_id
            s.commit()
        return bound_at

    # ---- locations ----
    def is_duplicate(self, device_id: str, seq: int) -> bool:
        with db.SessionLocal() as s:
            row = s.scalar(
                select(LocationRow.id).where(LocationRow.device_id == device_id, LocationRow.seq == seq)
            )
            return row is not None

    def add_location(self, device_id: str, pet_id: Optional[str], p: LocationPoint) -> LocationRecord:
        with db.SessionLocal() as s:
            row = LocationRow(
                device_id=device_id, pet_id=pet_id, seq=p.seq, ts=p.ts,
                dt=datetime.fromtimestamp(p.ts, tz=timezone.utc),
                lat=p.lat, lng=p.lng, accuracy_m=p.accuracy_m, source=p.source.value,
                speed_mps=p.speed_mps, heading=p.heading, battery_pct=p.battery_pct,
                motion_state=p.motion_state.value if p.motion_state else None,
            )
            s.add(row)
            s.commit()
            return _loc(row)

    def latest_for_pet(self, pet_id: str) -> Optional[LocationRecord]:
        with db.SessionLocal() as s:
            row = s.scalar(
                select(LocationRow).where(LocationRow.pet_id == pet_id)
                .order_by(LocationRow.ts.desc(), LocationRow.id.desc()).limit(1)
            )
            return _loc(row) if row else None

    def trail(self, pet_id: str, start: datetime, end: datetime) -> List[LocationRecord]:
        start, end = _as_utc(start), _as_utc(end)
        with db.SessionLocal() as s:
            rows = s.scalars(
                select(LocationRow).where(
                    LocationRow.pet_id == pet_id,
                    LocationRow.dt >= start.replace(tzinfo=None),
                    LocationRow.dt <= end.replace(tzinfo=None),
                ).order_by(LocationRow.ts.asc())
            ).all()
            return [_loc(r) for r in rows]

    # ---- device status / events ----
    def touch_device(self, device_id: str, *, mode: Optional[str] = None,
                     battery_pct: Optional[int] = None) -> DeviceStatusRecord:
        with db.SessionLocal() as s:
            row = s.get(DeviceStatusRow, device_id)
            if row is None:
                row = DeviceStatusRow(device_id=device_id, mode=mode or "idle")
                s.add(row)
            row.last_seen = utcnow()
            if mode is not None:
                row.mode = mode
            if battery_pct is not None:
                row.battery_pct = battery_pct
            s.commit()
            return _status(row)

    def get_device_status(self, device_id: str) -> Optional[DeviceStatusRecord]:
        with db.SessionLocal() as s:
            r = s.get(DeviceStatusRow, device_id)
            return _status(r) if r else None

    def all_device_status(self) -> List[DeviceStatusRecord]:
        with db.SessionLocal() as s:
            return [_status(r) for r in s.scalars(select(DeviceStatusRow)).all()]

    def add_device_event(self, device_id: str, ts: int, event: str, data: Optional[dict]) -> None:
        with db.SessionLocal() as s:
            s.add(DeviceEventRow(device_id=device_id, ts=ts, event=event, data=data))
            s.commit()

    # ---- geofences ----
    def create_geofence(self, pet_id: str, name: str, center_lat: float, center_lng: float,
                        radius_m: float, enabled: bool) -> GeofenceRecord:
        gid = gen_id("geo")
        with db.SessionLocal() as s:
            s.add(GeofenceRow(
                id=gid, pet_id=pet_id, name=name, center_lat=center_lat, center_lng=center_lng,
                radius_m=radius_m, enabled=enabled, consecutive_outside=0, open_alert_id=None,
            ))
            s.commit()
        return GeofenceRecord(gid, pet_id, name, center_lat, center_lng, radius_m, enabled)

    def geofences_for_pet(self, pet_id: str) -> List[GeofenceRecord]:
        with db.SessionLocal() as s:
            rows = s.scalars(select(GeofenceRow).where(GeofenceRow.pet_id == pet_id)).all()
            return [_gf(r) for r in rows]

    def update_geofence_state(self, geo_id: str, consecutive_outside: int, open_alert_id: Optional[str]) -> None:
        with db.SessionLocal() as s:
            row = s.get(GeofenceRow, geo_id)
            if row:
                row.consecutive_outside = consecutive_outside
                row.open_alert_id = open_alert_id
                s.commit()

    # ---- alerts ----
    def create_alert(self, *, user_id: str, pet_id: str, device_id: Optional[str], type_: str,
                     severity: str, message: str, location_point_id: Optional[int]) -> AlertRecord:
        rec = AlertRecord(
            id=gen_id("alt"), user_id=user_id, pet_id=pet_id, device_id=device_id, type=type_,
            severity=severity, status="open", message=message,
            location_point_id=location_point_id, created_at=utcnow(),
        )
        with db.SessionLocal() as s:
            s.add(AlertRow(
                id=rec.id, user_id=user_id, pet_id=pet_id, device_id=device_id, type=type_,
                severity=severity, status="open", message=message,
                location_point_id=location_point_id, created_at=rec.created_at,
            ))
            s.commit()
        return rec

    def open_alert(self, pet_id: str, type_: str) -> Optional[AlertRecord]:
        with db.SessionLocal() as s:
            row = s.scalar(select(AlertRow).where(
                AlertRow.pet_id == pet_id, AlertRow.type == type_, AlertRow.status == "open",
            ))
            return _alert(row) if row else None

    def alerts_for_owner(self, owner_id: str, status: Optional[str] = None, limit: int = 50) -> List[AlertRecord]:
        with db.SessionLocal() as s:
            q = select(AlertRow).where(AlertRow.user_id == owner_id)
            if status:
                q = q.where(AlertRow.status == status)
            q = q.order_by(AlertRow.created_at.desc()).limit(limit)
            return [_alert(r) for r in s.scalars(q).all()]

    def find_alert(self, alert_id: str) -> Optional[AlertRecord]:
        with db.SessionLocal() as s:
            r = s.get(AlertRow, alert_id)
            return _alert(r) if r else None

    def set_alert_status(self, alert_id: str, status: str,
                        acknowledged_at: Optional[datetime] = None) -> Optional[AlertRecord]:
        with db.SessionLocal() as s:
            row = s.get(AlertRow, alert_id)
            if not row:
                return None
            row.status = status
            if acknowledged_at is not None:
                row.acknowledged_at = acknowledged_at
            s.commit()
            return _alert(row)


store = Store()
