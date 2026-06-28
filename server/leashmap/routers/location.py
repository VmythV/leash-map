"""Latest location and trail queries."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from ..analytics import activity_summary
from ..config import settings
from ..deps import app_auth, get_store
from ..geo import douglas_peucker, haversine_m
from ..schemas import ActivitySummary, LatestLocation, Trail, User
from ..store import to_iso
from ..web import owned_pet, to_app_location, to_device_status

router = APIRouter(prefix="/v1/pets", tags=["location"])


@router.get("/{pet_id}/location/latest", response_model=LatestLocation)
def latest_location(pet_id: str, user: User = Depends(app_auth), store=Depends(get_store)):
    pet = owned_pet(store, user, pet_id)
    rec = store.latest_for_pet(pet_id)
    st = store.get_device_status(pet.device_id) if pet.device_id else None
    return LatestLocation(
        pet_id=pet_id,
        location=to_app_location(rec) if rec else None,
        device=to_device_status(st),
    )


@router.get("/{pet_id}/trail", response_model=Trail)
def trail(
    pet_id: str,
    from_: datetime = Query(alias="from"),
    to: datetime = Query(...),
    downsample: bool = Query(default=True),
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    owned_pet(store, user, pet_id)
    recs = store.trail(pet_id, from_, to)

    # distance is computed on the full-resolution trail
    distance = 0.0
    for a, b in zip(recs, recs[1:]):
        distance += haversine_m(a.lat, a.lng, b.lat, b.lng)

    if downsample and len(recs) > 2:
        keep = douglas_peucker([(r.lat, r.lng) for r in recs], settings.trail_downsample_epsilon_m)
        recs = [recs[i] for i in keep]

    return Trail(
        pet_id=pet_id,
        from_=to_iso(from_),
        to=to_iso(to),
        point_count=len(recs),
        distance_m=round(distance, 1),
        points=[to_app_location(r) for r in recs],
    )


@router.get("/{pet_id}/activity", response_model=ActivitySummary)
def activity(
    pet_id: str,
    from_: datetime = Query(alias="from"),
    to: datetime = Query(...),
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    owned_pet(store, user, pet_id)
    recs = store.trail(pet_id, from_, to)
    summary = activity_summary(recs)
    return ActivitySummary(
        pet_id=pet_id,
        from_=to_iso(from_),
        to=to_iso(to),
        **summary,
    )
