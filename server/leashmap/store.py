"""In-memory store (MVP placeholder for PostgreSQL/PostGIS).

Holds all state in process. Not durable, not multi-process. The router and
service layers depend only on these methods, so swapping in a real database
later does not change call sites.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .ids import gen_id
from .schemas import Mode, User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
    enabled: bool = True


@dataclass
class GeofenceState:
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
    mode: str = Mode.idle.value
    battery_pct: Optional[int] = None
    last_seen: Optional[datetime] = None


@dataclass
class PetRecord:
    id: str
    owner_id: str
    name: str
    species: str
    device_id: Optional[str] = None


class Store:
    def __init__(self) -> None:
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, str] = {}  # token -> user_id
        self.pets: Dict[str, PetRecord] = {}
        self.device_to_pet: Dict[str, str] = {}
        self.bindings_bound_at: Dict[str, datetime] = {}  # device_id -> bound_at
        self.locations: List[LocationRecord] = []
        self.latest_by_pet: Dict[str, LocationRecord] = {}
        self.seen_seq: Dict[str, set] = {}  # device_id -> set[seq]
        self.geofences: Dict[str, GeofenceRecord] = {}
        self.geofence_state: Dict[str, GeofenceState] = {}
        self.alerts: List[AlertRecord] = []
        self.device_status: Dict[str, DeviceStatusRecord] = {}
        self.pending_commands: Dict[str, list] = {}
        self._loc_seq = 0

    def reset(self) -> None:
        self.__init__()

    # ---- users / sessions ----
    def create_demo_user(self, display_name: Optional[str]) -> "tuple[User, str]":
        user = User(id=gen_id("usr"), display_name=display_name)
        self.users[user.id] = user
        token = "sess_" + gen_id("", 16).lstrip("_")
        self.sessions[token] = user.id
        return user, token

    def user_for_session(self, token: str) -> Optional[User]:
        uid = self.sessions.get(token)
        return self.users.get(uid) if uid else None

    # ---- pets / bindings ----
    def create_pet(self, owner_id: str, name: str, species: str) -> PetRecord:
        pet = PetRecord(id=gen_id("pet"), owner_id=owner_id, name=name, species=species)
        self.pets[pet.id] = pet
        return pet

    def pets_for_owner(self, owner_id: str) -> List[PetRecord]:
        return [p for p in self.pets.values() if p.owner_id == owner_id]

    def bind(self, device_id: str, pet_id: str) -> datetime:
        pet = self.pets[pet_id]
        # unbind any previous pet on this device
        prev = self.device_to_pet.get(device_id)
        if prev and prev in self.pets:
            self.pets[prev].device_id = None
        pet.device_id = device_id
        self.device_to_pet[device_id] = pet_id
        bound_at = utcnow()
        self.bindings_bound_at[device_id] = bound_at
        return bound_at

    def pet_for_device(self, device_id: str) -> Optional[str]:
        return self.device_to_pet.get(device_id)

    # ---- locations ----
    def next_location_id(self) -> int:
        self._loc_seq += 1
        return self._loc_seq

    def is_duplicate(self, device_id: str, seq: int) -> bool:
        return seq in self.seen_seq.get(device_id, set())

    def add_location(self, rec: LocationRecord) -> None:
        self.locations.append(rec)
        self.seen_seq.setdefault(rec.device_id, set()).add(rec.seq)
        if rec.pet_id:
            cur = self.latest_by_pet.get(rec.pet_id)
            if cur is None or rec.ts >= cur.ts:
                self.latest_by_pet[rec.pet_id] = rec

    def trail(self, pet_id: str, start: datetime, end: datetime) -> List[LocationRecord]:
        out = [
            r for r in self.locations
            if r.pet_id == pet_id and start <= r.dt <= end
        ]
        out.sort(key=lambda r: r.ts)
        return out

    # ---- device status ----
    def touch_device(
        self,
        device_id: str,
        *,
        mode: Optional[str] = None,
        battery_pct: Optional[int] = None,
    ) -> DeviceStatusRecord:
        st = self.device_status.setdefault(device_id, DeviceStatusRecord(device_id=device_id))
        st.last_seen = utcnow()
        if mode is not None:
            st.mode = mode
        if battery_pct is not None:
            st.battery_pct = battery_pct
        return st

    # ---- geofences ----
    def create_geofence(self, gf: GeofenceRecord) -> GeofenceRecord:
        self.geofences[gf.id] = gf
        self.geofence_state[gf.id] = GeofenceState()
        return gf

    def geofences_for_pet(self, pet_id: str) -> List[GeofenceRecord]:
        return [g for g in self.geofences.values() if g.pet_id == pet_id]

    # ---- alerts ----
    def add_alert(self, alert: AlertRecord) -> None:
        self.alerts.append(alert)

    def open_alert(self, pet_id: str, type_: str) -> Optional[AlertRecord]:
        for a in self.alerts:
            if a.pet_id == pet_id and a.type == type_ and a.status == "open":
                return a
        return None

    def alerts_for_owner(self, owner_id: str, status: Optional[str] = None) -> List[AlertRecord]:
        out = [a for a in self.alerts if a.user_id == owner_id]
        if status:
            out = [a for a in out if a.status == status]
        out.sort(key=lambda a: a.created_at, reverse=True)
        return out

    def find_alert(self, alert_id: str) -> Optional[AlertRecord]:
        for a in self.alerts:
            if a.id == alert_id:
                return a
        return None


store = Store()
