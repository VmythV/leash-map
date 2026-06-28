"""Circular safe zones."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..deps import app_auth, get_store
from ..errors import APIError
from ..schemas import Geofence, GeofenceCreate, GeofenceUpdate, User
from ..store import GeofenceRecord
from ..web import owned_pet

router = APIRouter(prefix="/v1/pets", tags=["geofence"])


def _to_geofence(rec: GeofenceRecord) -> Geofence:
    return Geofence(
        id=rec.id,
        pet_id=rec.pet_id,
        name=rec.name,
        center_lat=rec.center_lat,
        center_lng=rec.center_lng,
        radius_m=rec.radius_m,
        enabled=rec.enabled,
        alert_on_exit=rec.alert_on_exit,
        alert_on_enter=rec.alert_on_enter,
        active_start=rec.active_start,
        active_end=rec.active_end,
    )


@router.get("/{pet_id}/geofences")
def list_geofences(pet_id: str, user: User = Depends(app_auth), store=Depends(get_store)):
    owned_pet(store, user, pet_id)
    data: List[Geofence] = [_to_geofence(g) for g in store.geofences_for_pet(pet_id)]
    return {"data": data}


@router.post("/{pet_id}/geofences", response_model=Geofence, status_code=201)
def create_geofence(
    pet_id: str,
    body: GeofenceCreate,
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    owned_pet(store, user, pet_id)
    rec = store.create_geofence(
        pet_id=pet_id,
        name=body.name,
        center_lat=body.center_lat,
        center_lng=body.center_lng,
        radius_m=body.radius_m,
        enabled=body.enabled,
        alert_on_exit=body.alert_on_exit,
        alert_on_enter=body.alert_on_enter,
    )
    return _to_geofence(rec)


@router.patch("/{pet_id}/geofences/{geo_id}", response_model=Geofence)
def update_geofence(
    pet_id: str,
    geo_id: str,
    body: GeofenceUpdate,
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    owned_pet(store, user, pet_id)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    rec = store.update_geofence(geo_id, **fields)
    if rec is None or rec.pet_id != pet_id:
        raise APIError("not_found", "Geofence not found")
    return _to_geofence(rec)
