"""Pydantic schemas mirroring docs/api/openapi.yaml."""
from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------- Enums ----------------
class Source(str, Enum):
    gnss = "gnss"
    cell = "cell"
    wifi = "wifi"
    ble = "ble"
    simulator = "simulator"


class MotionState(str, Enum):
    still = "still"
    moving = "moving"
    unknown = "unknown"


class Mode(str, Enum):
    idle = "idle"
    tracking = "tracking"
    guard = "guard"
    lost = "lost"
    low_battery = "low_battery"


class Species(str, Enum):
    dog = "dog"
    cat = "cat"
    other = "other"


class AlertType(str, Enum):
    exit_zone = "exit_zone"
    low_battery = "low_battery"
    offline = "offline"


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertStatus(str, Enum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"


# ---------------- Device uplink ----------------
class LocationPoint(BaseModel):
    seq: int
    ts: int = Field(description="Unix epoch seconds")
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(ge=0)
    source: Source
    speed_mps: Optional[float] = None
    heading: Optional[int] = Field(default=None, ge=0, le=359)
    battery_pct: Optional[int] = Field(default=None, ge=0, le=100)
    motion_state: Optional[MotionState] = None


class LocationUpload(LocationPoint):
    type: Literal["location"]
    protocol_version: Literal[1]
    device_id: str


class LocationBatchUpload(BaseModel):
    type: Literal["location_batch"]
    protocol_version: Literal[1]
    device_id: str
    ts: int
    points: List[LocationPoint] = Field(max_length=200)


class Network(BaseModel):
    type: Optional[str] = None
    rssi: Optional[int] = None


class Heartbeat(BaseModel):
    type: Literal["heartbeat"]
    protocol_version: Literal[1]
    device_id: str
    ts: int
    battery_pct: int = Field(ge=0, le=100)
    mode: Mode
    network: Optional[Network] = None
    firmware_version: Optional[str] = None


class DeviceEvent(BaseModel):
    type: Literal["event"]
    protocol_version: Literal[1]
    device_id: str
    ts: int
    event: str
    data: Optional[dict] = None


class Command(BaseModel):
    command_id: str
    type: str
    params: Optional[dict] = None
    expires_at: int


class IngestResponse(BaseModel):
    ok: bool = True
    accepted: int = 0
    duplicated: int = 0
    rejected: int = 0
    server_ts: str
    commands: List[Command] = Field(default_factory=list)


# ---------------- App: auth / pets ----------------
class DemoSessionRequest(BaseModel):
    display_name: Optional[str] = None


class User(BaseModel):
    id: str
    display_name: Optional[str] = None


class DemoSessionResponse(BaseModel):
    token: str
    user: User


class PetCreate(BaseModel):
    name: str
    species: Species = Species.dog


class Pet(BaseModel):
    id: str
    name: str
    species: Species
    device_id: Optional[str] = None
    last_location_at: Optional[str] = None


class BindRequest(BaseModel):
    device_id: str
    pet_id: str


class DeviceBinding(BaseModel):
    device_id: str
    pet_id: str
    bound_at: str


# ---------------- App: location ----------------
class AppLocation(BaseModel):
    ts: str
    lat: float
    lng: float
    accuracy_m: float
    source: Source
    speed_mps: Optional[float] = None
    heading: Optional[int] = None
    motion_state: Optional[MotionState] = None


class DeviceStatus(BaseModel):
    device_id: str
    online: bool
    mode: Mode
    battery_pct: Optional[int] = None
    last_seen_at: Optional[str] = None


class LatestLocation(BaseModel):
    pet_id: str
    location: Optional[AppLocation] = None
    device: Optional[DeviceStatus] = None


class Trail(BaseModel):
    pet_id: str
    from_: str = Field(serialization_alias="from")
    to: str
    point_count: int
    distance_m: float
    points: List[AppLocation]


class Stop(BaseModel):
    lat: float
    lng: float
    count: int
    duration_s: int


class ActivitySummary(BaseModel):
    pet_id: str
    from_: str = Field(serialization_alias="from")
    to: str
    point_count: int
    distance_m: float
    moving_points: int
    active_minutes: float
    by_hour_m: List[float]
    stops: List[Stop]


# ---------------- App: geofence ----------------
class GeofenceCreate(BaseModel):
    name: str
    center_lat: float = Field(ge=-90, le=90)
    center_lng: float = Field(ge=-180, le=180)
    radius_m: float = Field(ge=20)
    enabled: bool = True


class Geofence(GeofenceCreate):
    id: str
    pet_id: str


# ---------------- App: alerts ----------------
class Alert(BaseModel):
    id: str
    pet_id: str
    device_id: Optional[str] = None
    type: AlertType
    severity: Severity
    status: AlertStatus
    message: str
    location_point_id: Optional[int] = None
    created_at: str
    acknowledged_at: Optional[str] = None
