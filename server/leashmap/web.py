"""Shared helpers for App-facing routers: access checks + converters."""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from .errors import APIError
from .schemas import AppLocation, DeviceStatus, Mode, User
from .store import DeviceStatusRecord, LocationRecord, PetRecord, Store, to_iso, utcnow

# Online if a heartbeat/location was seen within this window (MVP: normal mode).
ONLINE_WINDOW = timedelta(minutes=30)


def owned_pet(store: Store, user: User, pet_id: str) -> PetRecord:
    pet = store.pets.get(pet_id)
    if pet is None:
        raise APIError("not_found", "Pet not found")
    if pet.owner_id != user.id:
        raise APIError("permission_denied", "Pet does not belong to user")
    return pet


def to_app_location(rec: LocationRecord) -> AppLocation:
    return AppLocation(
        ts=to_iso(rec.dt),
        lat=rec.lat,
        lng=rec.lng,
        accuracy_m=rec.accuracy_m,
        source=rec.source,
        speed_mps=rec.speed_mps,
        heading=rec.heading,
        motion_state=rec.motion_state,
    )


def to_device_status(st: Optional[DeviceStatusRecord]) -> Optional[DeviceStatus]:
    if st is None:
        return None
    online = st.last_seen is not None and (utcnow() - st.last_seen) < ONLINE_WINDOW
    return DeviceStatus(
        device_id=st.device_id,
        online=online,
        mode=Mode(st.mode),
        battery_pct=st.battery_pct,
        last_seen_at=to_iso(st.last_seen) if st.last_seen else None,
    )
