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
    pet = store.get_pet(pet_id)
    if pet is None:
        raise APIError("not_found", "Pet not found")
    if pet.owner_id != user.id:
        raise APIError("permission_denied", "Pet does not belong to user")
    return pet


def viewable_pet(store: Store, user: User, pet_id: str) -> PetRecord:
    """Read access: the owner or a user the pet is shared with."""
    pet = store.get_pet(pet_id)
    if pet is None:
        raise APIError("not_found", "Pet not found")
    if pet.owner_id == user.id or store.is_shared_with(pet_id, user.id):
        return pet
    raise APIError("permission_denied", "Pet is not visible to this user")


def owned_device(store: Store, user: User, device_id: str) -> PetRecord:
    """Resolve a device to its bound pet and verify the user owns it."""
    pet_id = store.pet_for_device(device_id)
    if pet_id is None:
        raise APIError("not_found", "Device is not bound")
    return owned_pet(store, user, pet_id)


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
