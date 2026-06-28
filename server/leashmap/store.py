"""Persistence store over SQLAlchemy (SQLite for MVP).

Returns detached DTO dataclasses so the router/service layers never touch ORM
sessions. Each method is a small unit of work that commits on success. Swapping
SQLite for PostgreSQL is a URL change only (see config / db).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import delete, select

from . import db
from .db import (
    AlertRow,
    BindingRow,
    CommandRow,
    DeviceConfigRow,
    DeviceEventRow,
    DeviceStatusRow,
    GeofenceRow,
    LocationRow,
    NotificationDeliveryRow,
    PetRow,
    PetSettingsRow,
    PetShareRow,
    SessionRow,
    UserRow,
)
from datetime import timedelta
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
    alert_on_exit: bool = True
    alert_on_enter: bool = False
    active_start: Optional[int] = None
    active_end: Optional[int] = None
    consecutive_outside: int = 0
    open_alert_id: Optional[str] = None
    last_inside: Optional[bool] = None


@dataclass
class PetSettingsRecord:
    pet_id: str
    exit_enabled: bool = True
    enter_enabled: bool = False
    low_battery_enabled: bool = True
    offline_enabled: bool = True
    low_battery_threshold: Optional[int] = None
    quiet_start: Optional[int] = None
    quiet_end: Optional[int] = None
    timezone: str = "UTC"
    tracking_paused: bool = False
    retention_days: int = 30


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


@dataclass
class DeviceConfigRecord:
    device_id: str
    led_pattern: str = "blink"
    led_morse: str = "SOS"
    report_interval_s: Optional[int] = None
    power_mode: str = "normal"


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
        alert_on_exit=r.alert_on_exit, alert_on_enter=r.alert_on_enter,
        active_start=r.active_start, active_end=r.active_end,
        consecutive_outside=r.consecutive_outside, open_alert_id=r.open_alert_id,
        last_inside=r.last_inside,
    )


def _settings(r: PetSettingsRow) -> PetSettingsRecord:
    return PetSettingsRecord(
        pet_id=r.pet_id, exit_enabled=r.exit_enabled, enter_enabled=r.enter_enabled,
        low_battery_enabled=r.low_battery_enabled, offline_enabled=r.offline_enabled,
        low_battery_threshold=r.low_battery_threshold,
        quiet_start=r.quiet_start, quiet_end=r.quiet_end, timezone=r.timezone,
        tracking_paused=r.tracking_paused, retention_days=r.retention_days,
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

    def get_user(self, user_id: str) -> Optional[User]:
        with db.SessionLocal() as s:
            u = s.get(UserRow, user_id)
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

    # ---- sharing ----
    def add_share(self, pet_id: str, user_id: str) -> None:
        with db.SessionLocal() as s:
            if s.get(PetShareRow, (pet_id, user_id)) is None:
                s.add(PetShareRow(pet_id=pet_id, user_id=user_id, created_at=utcnow()))
                s.commit()

    def remove_share(self, pet_id: str, user_id: str) -> None:
        with db.SessionLocal() as s:
            row = s.get(PetShareRow, (pet_id, user_id))
            if row:
                s.delete(row)
                s.commit()

    def shares_for_pet(self, pet_id: str) -> List[str]:
        with db.SessionLocal() as s:
            return [r.user_id for r in s.scalars(
                select(PetShareRow).where(PetShareRow.pet_id == pet_id)).all()]

    def is_shared_with(self, pet_id: str, user_id: str) -> bool:
        with db.SessionLocal() as s:
            return s.get(PetShareRow, (pet_id, user_id)) is not None

    def pets_shared_with(self, user_id: str) -> List[PetRecord]:
        with db.SessionLocal() as s:
            pet_ids = [r.pet_id for r in s.scalars(
                select(PetShareRow).where(PetShareRow.user_id == user_id)).all()]
            return [_pet(s.get(PetRow, pid)) for pid in pet_ids if s.get(PetRow, pid)]

    def bind(self, device_id: str, pet_id: str) -> datetime:
        """Bind a device to a pet. A pet may hold many devices; a device maps to
        one pet. pet.device_id tracks the most-recently-bound "primary" device.
        """
        bound_at = utcnow()
        with db.SessionLocal() as s:
            row = s.get(BindingRow, device_id)
            if row is None:
                s.add(BindingRow(device_id=device_id, pet_id=pet_id, bound_at=bound_at))
            else:
                if row.pet_id != pet_id:
                    # moving from another pet (router normally blocks this)
                    prev_pet = s.get(PetRow, row.pet_id)
                    if prev_pet and prev_pet.device_id == device_id:
                        prev_pet.device_id = None
                    row.pet_id = pet_id
                row.bound_at = bound_at
            pet = s.get(PetRow, pet_id)
            if pet:
                pet.device_id = device_id  # primary = last bound
            s.commit()
        return bound_at

    def devices_for_pet(self, pet_id: str) -> "list[tuple[str, datetime]]":
        with db.SessionLocal() as s:
            rows = s.scalars(
                select(BindingRow).where(BindingRow.pet_id == pet_id)
                .order_by(BindingRow.bound_at.asc())
            ).all()
            return [(r.device_id, _as_utc(r.bound_at)) for r in rows]

    def unbind(self, device_id: str) -> bool:
        with db.SessionLocal() as s:
            row = s.get(BindingRow, device_id)
            if row is None:
                return False
            pet = s.get(PetRow, row.pet_id)
            s.delete(row)
            s.flush()
            if pet and pet.device_id == device_id:
                remaining = s.scalar(
                    select(BindingRow).where(BindingRow.pet_id == pet.id)
                    .order_by(BindingRow.bound_at.desc()).limit(1)
                )
                pet.device_id = remaining.device_id if remaining else None
            s.commit()
            return True

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

    def purge_expired_locations(self, now: datetime) -> int:
        """Delete location points older than each pet's retention window."""
        total = 0
        with db.SessionLocal() as s:
            for pet in s.scalars(select(PetRow)).all():
                settings = s.get(PetSettingsRow, pet.id)
                days = settings.retention_days if settings else 30
                cutoff = (now - timedelta(days=days)).replace(tzinfo=None)
                res = s.execute(
                    delete(LocationRow).where(
                        LocationRow.pet_id == pet.id, LocationRow.dt < cutoff)
                )
                total += res.rowcount or 0
            s.commit()
        return total

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
                        radius_m: float, enabled: bool, alert_on_exit: bool = True,
                        alert_on_enter: bool = False) -> GeofenceRecord:
        gid = gen_id("geo")
        with db.SessionLocal() as s:
            s.add(GeofenceRow(
                id=gid, pet_id=pet_id, name=name, center_lat=center_lat, center_lng=center_lng,
                radius_m=radius_m, enabled=enabled, alert_on_exit=alert_on_exit,
                alert_on_enter=alert_on_enter, consecutive_outside=0, open_alert_id=None,
            ))
            s.commit()
        return GeofenceRecord(gid, pet_id, name, center_lat, center_lng, radius_m, enabled,
                              alert_on_exit=alert_on_exit, alert_on_enter=alert_on_enter)

    def geofences_for_pet(self, pet_id: str) -> List[GeofenceRecord]:
        with db.SessionLocal() as s:
            rows = s.scalars(select(GeofenceRow).where(GeofenceRow.pet_id == pet_id)).all()
            return [_gf(r) for r in rows]

    def update_geofence(self, geo_id: str, **fields) -> Optional[GeofenceRecord]:
        with db.SessionLocal() as s:
            row = s.get(GeofenceRow, geo_id)
            if row is None:
                return None
            for k, v in fields.items():
                setattr(row, k, v)
            s.commit()
            return _gf(row)

    def update_geofence_state(self, geo_id: str, consecutive_outside: int,
                              open_alert_id: Optional[str], last_inside: Optional[bool] = None) -> None:
        with db.SessionLocal() as s:
            row = s.get(GeofenceRow, geo_id)
            if row:
                row.consecutive_outside = consecutive_outside
                row.open_alert_id = open_alert_id
                if last_inside is not None:
                    row.last_inside = last_inside
                s.commit()

    # ---- pet settings ----
    def get_pet_settings(self, pet_id: str) -> PetSettingsRecord:
        with db.SessionLocal() as s:
            r = s.get(PetSettingsRow, pet_id)
            return _settings(r) if r else PetSettingsRecord(pet_id=pet_id)

    def update_pet_settings(self, pet_id: str, **fields) -> PetSettingsRecord:
        with db.SessionLocal() as s:
            row = s.get(PetSettingsRow, pet_id)
            if row is None:
                row = PetSettingsRow(pet_id=pet_id)
                s.add(row)
            for k, v in fields.items():
                if v is not None:
                    setattr(row, k, v)
            s.commit()
            return _settings(row)

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

    def alerts_for_viewer(self, user_id: str, status: Optional[str] = None, limit: int = 50) -> List[AlertRecord]:
        """Alerts for every pet the user can view (owned + shared)."""
        with db.SessionLocal() as s:
            owned = [p.id for p in s.scalars(select(PetRow).where(PetRow.owner_id == user_id)).all()]
            shared = [r.pet_id for r in s.scalars(
                select(PetShareRow).where(PetShareRow.user_id == user_id)).all()]
            pet_ids = set(owned) | set(shared)
            if not pet_ids:
                return []
            q = select(AlertRow).where(AlertRow.pet_id.in_(pet_ids))
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

    # ---- notification deliveries ----
    def record_delivery(self, alert_id: str, user_id: str, channel: str, status: str) -> None:
        with db.SessionLocal() as s:
            s.add(NotificationDeliveryRow(
                alert_id=alert_id, user_id=user_id, channel=channel,
                status=status, created_at=utcnow(),
            ))
            s.commit()

    def deliveries_for_alert(self, alert_id: str) -> List[dict]:
        with db.SessionLocal() as s:
            rows = s.scalars(
                select(NotificationDeliveryRow).where(NotificationDeliveryRow.alert_id == alert_id)
            ).all()
            return [{"channel": r.channel, "status": r.status, "created_at": to_iso(r.created_at)} for r in rows]

    # ---- downlink commands ----
    def enqueue_command(self, device_id: str, type_: str, params: Optional[dict], expires_at: int) -> dict:
        cid = gen_id("cmd", 8)
        with db.SessionLocal() as s:
            s.add(CommandRow(
                command_id=cid, device_id=device_id, type=type_, params=params,
                expires_at=expires_at, status="pending", created_at=utcnow(),
            ))
            s.commit()
        return {"command_id": cid, "type": type_, "params": params, "expires_at": expires_at}

    def pending_commands(self, device_id: str, now_epoch: int) -> List[dict]:
        with db.SessionLocal() as s:
            rows = s.scalars(select(CommandRow).where(
                CommandRow.device_id == device_id,
                CommandRow.status == "pending",
                CommandRow.expires_at > now_epoch,
            )).all()
            return [
                {"command_id": r.command_id, "type": r.type, "params": r.params, "expires_at": r.expires_at}
                for r in rows
            ]

    # ---- device config ----
    def get_device_config(self, device_id: str) -> DeviceConfigRecord:
        with db.SessionLocal() as s:
            r = s.get(DeviceConfigRow, device_id)
            if r is None:
                return DeviceConfigRecord(device_id=device_id)
            return DeviceConfigRecord(
                device_id=r.device_id, led_pattern=r.led_pattern, led_morse=r.led_morse,
                report_interval_s=r.report_interval_s, power_mode=r.power_mode,
            )

    def update_device_config(self, device_id: str, **fields) -> DeviceConfigRecord:
        with db.SessionLocal() as s:
            r = s.get(DeviceConfigRow, device_id)
            if r is None:
                r = DeviceConfigRow(device_id=device_id)
                s.add(r)
            for k, v in fields.items():
                if v is not None:
                    setattr(r, k, v)
            s.commit()
            return DeviceConfigRecord(
                device_id=r.device_id, led_pattern=r.led_pattern, led_morse=r.led_morse,
                report_interval_s=r.report_interval_s, power_mode=r.power_mode,
            )

    def ack_command(self, command_id: str, status: str = "applied") -> bool:
        with db.SessionLocal() as s:
            row = s.get(CommandRow, command_id)
            if row is None or row.status == "acked":
                return False
            row.status = "acked"
            row.acked_at = utcnow()
            s.commit()
            return True


store = Store()
