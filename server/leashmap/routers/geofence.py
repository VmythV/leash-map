"""Circular safe zones."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..deps import app_auth, get_store
from ..schemas import Geofence, GeofenceCreate, User
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
    )
    return _to_geofence(rec)
