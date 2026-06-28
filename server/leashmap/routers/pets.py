"""Pets and device binding."""
from __future__ import annotations

import time
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..deps import app_auth, get_store
from ..errors import APIError
from ..schemas import (
    AlertSettings,
    AlertSettingsUpdate,
    BindRequest,
    DeviceBinding,
    DeviceConfig,
    DeviceConfigUpdate,
    Pet,
    PetCreate,
    ShareRequest,
    User,
)
from ..store import to_iso
from ..web import owned_device, owned_pet

router = APIRouter(prefix="/v1", tags=["pets"])


def _to_pet(store, rec, shared: bool = False) -> Pet:
    latest = store.latest_for_pet(rec.id)
    return Pet(
        id=rec.id,
        name=rec.name,
        species=rec.species,
        device_id=rec.device_id,
        last_location_at=to_iso(latest.dt) if latest else None,
        shared=shared,
    )


@router.get("/pets")
def list_pets(user: User = Depends(app_auth), store=Depends(get_store)):
    data: List[Pet] = [_to_pet(store, p) for p in store.pets_for_owner(user.id)]
    data += [_to_pet(store, p, shared=True) for p in store.pets_shared_with(user.id)]
    return {"data": data, "page": {"next_cursor": None}}


@router.get("/pets/{pet_id}/shares")
def list_shares(pet_id: str, user: User = Depends(app_auth), store=Depends(get_store)):
    owned_pet(store, user, pet_id)  # only the owner manages shares
    return {"data": store.shares_for_pet(pet_id)}


@router.post("/pets/{pet_id}/shares")
def add_share(pet_id: str, body: ShareRequest, user: User = Depends(app_auth), store=Depends(get_store)):
    owned_pet(store, user, pet_id)
    if store.get_user(body.user_id) is None:
        raise APIError("not_found", "Target user not found")
    if body.user_id == user.id:
        raise APIError("invalid_argument", "Cannot share with yourself")
    store.add_share(pet_id, body.user_id)
    return {"ok": True, "shares": store.shares_for_pet(pet_id)}


@router.delete("/pets/{pet_id}/shares/{user_id}")
def remove_share(pet_id: str, user_id: str, user: User = Depends(app_auth), store=Depends(get_store)):
    owned_pet(store, user, pet_id)
    store.remove_share(pet_id, user_id)
    return {"ok": True, "shares": store.shares_for_pet(pet_id)}


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


def _to_settings(rec) -> AlertSettings:
    return AlertSettings(
        pet_id=rec.pet_id,
        exit_enabled=rec.exit_enabled,
        enter_enabled=rec.enter_enabled,
        low_battery_enabled=rec.low_battery_enabled,
        offline_enabled=rec.offline_enabled,
        low_battery_threshold=rec.low_battery_threshold,
        quiet_start=rec.quiet_start,
        quiet_end=rec.quiet_end,
        tracking_paused=rec.tracking_paused,
        retention_days=rec.retention_days,
    )


@router.get("/pets/{pet_id}/alert-settings", response_model=AlertSettings)
def get_alert_settings(pet_id: str, user: User = Depends(app_auth), store=Depends(get_store)):
    owned_pet(store, user, pet_id)
    return _to_settings(store.get_pet_settings(pet_id))


@router.put("/pets/{pet_id}/alert-settings", response_model=AlertSettings)
def update_alert_settings(
    pet_id: str,
    body: AlertSettingsUpdate,
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    owned_pet(store, user, pet_id)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    return _to_settings(store.update_pet_settings(pet_id, **fields))


def _to_device_config(rec) -> DeviceConfig:
    return DeviceConfig(
        device_id=rec.device_id,
        led_pattern=rec.led_pattern,
        led_morse=rec.led_morse,
        report_interval_s=rec.report_interval_s,
        power_mode=rec.power_mode,
    )


@router.get("/devices/{device_id}/config", response_model=DeviceConfig)
def get_device_config(device_id: str, user: User = Depends(app_auth), store=Depends(get_store)):
    owned_device(store, user, device_id)
    return _to_device_config(store.get_device_config(device_id))


@router.put("/devices/{device_id}/config", response_model=DeviceConfig)
def update_device_config(
    device_id: str,
    body: DeviceConfigUpdate,
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    owned_device(store, user, device_id)
    fields = {k: (v.value if hasattr(v, "value") else v)
              for k, v in body.model_dump().items() if v is not None}
    cfg = store.update_device_config(device_id, **fields)
    # push the resulting config to the device via a set_config command
    expires_at = int(time.time()) + 600
    store.enqueue_command(device_id, "set_config", {
        "led_pattern": cfg.led_pattern,
        "led_morse": cfg.led_morse,
        "report_interval_s": cfg.report_interval_s,
    }, expires_at)
    return _to_device_config(cfg)


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
