"""Pets and device binding."""
from __future__ import annotations

import time
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..deps import app_auth, get_store
from ..errors import APIError
from ..schemas import BindRequest, DeviceBinding, Pet, PetCreate, User
from ..store import to_iso
from ..web import owned_pet

router = APIRouter(prefix="/v1", tags=["pets"])


def _to_pet(store, rec) -> Pet:
    latest = store.latest_for_pet(rec.id)
    return Pet(
        id=rec.id,
        name=rec.name,
        species=rec.species,
        device_id=rec.device_id,
        last_location_at=to_iso(latest.dt) if latest else None,
    )


@router.get("/pets")
def list_pets(user: User = Depends(app_auth), store=Depends(get_store)):
    data: List[Pet] = [_to_pet(store, p) for p in store.pets_for_owner(user.id)]
    return {"data": data, "page": {"next_cursor": None}}


@router.post("/pets", response_model=Pet, status_code=201)
def create_pet(body: PetCreate, user: User = Depends(app_auth), store=Depends(get_store)):
    rec = store.create_pet(user.id, body.name, body.species.value)
    return _to_pet(store, rec)


@router.post("/devices/bind", response_model=DeviceBinding)
def bind_device(body: BindRequest, user: User = Depends(app_auth), store=Depends(get_store)):
    pet = store.get_pet(body.pet_id)
    if pet is None:
        raise APIError("not_found", "Pet not found")
    if pet.owner_id != user.id:
        raise APIError("permission_denied", "Pet does not belong to user")
    existing = store.pet_for_device(body.device_id)
    if existing and existing != body.pet_id:
        raise APIError("conflict", "Device is already bound to another pet")
    bound_at = store.bind(body.device_id, body.pet_id)
    return DeviceBinding(
        device_id=body.device_id,
        pet_id=body.pet_id,
        bound_at=to_iso(bound_at),
    )


class LostModeRequest(BaseModel):
    on: bool


@router.post("/pets/{pet_id}/lost-mode")
def set_lost_mode(
    pet_id: str,
    body: LostModeRequest,
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    """Enqueue a set_mode command toward the pet's device (lost-pet mode)."""
    pet = owned_pet(store, user, pet_id)
    if not pet.device_id:
        raise APIError("conflict", "No device bound to this pet")
    expires_at = int(time.time()) + 300
    mode = "lost" if body.on else "tracking"
    cmd = store.enqueue_command(pet.device_id, "set_mode", {"mode": mode}, expires_at)
    return {"ok": True, "command": cmd}
