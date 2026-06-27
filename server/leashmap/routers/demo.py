"""Local-only web demo: a self-contained live map driven over SSE.

Enabled only when LEASHMAP_APP_ENV=local (see main.create_app). Not part of the
public API contract — a developer convenience to *see* the system move.
"""
from __future__ import annotations

import asyncio
import itertools
import math
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..broker import broker as _broker
from ..deps import get_broker, get_store
from ..schemas import LocationPoint, Source
from ..services import ingest_location

router = APIRouter(tags=["demo"])

_STATIC = Path(__file__).resolve().parent.parent / "static"
_seq = itertools.count(int(time.time()))

# A safe zone in a Shanghai park, reused by the demo page.
DEMO_CENTER = (31.2304, 121.4737)
DEMO_RADIUS_M = 120.0
_M_PER_DEG = 111_320.0


def _offset(lat: float, lng: float, north_m: float, east_m: float) -> tuple[float, float]:
    dlat = north_m / _M_PER_DEG
    dlng = east_m / (_M_PER_DEG * math.cos(math.radians(lat)))
    return lat + dlat, lng + dlng


@router.get("/demo")
def demo_page():
    return FileResponse(_STATIC / "demo.html")


@router.post("/demo/seed")
def seed(store=Depends(get_store)):
    user, token = store.create_demo_user("Demo")
    pet = store.create_pet(user.id, "Buddy", "dog")
    device_id = "dev_demo_" + token[-6:]
    store.bind(device_id, pet.id)
    gf = store.create_geofence(
        pet_id=pet.id, name="家",
        center_lat=DEMO_CENTER[0], center_lng=DEMO_CENTER[1],
        radius_m=DEMO_RADIUS_M, enabled=True,
    )
    return {
        "token": token,
        "pet_id": pet.id,
        "device_id": device_id,
        "geofence": {
            "center_lat": gf.center_lat,
            "center_lng": gf.center_lng,
            "radius_m": gf.radius_m,
        },
    }


class RunRequest(BaseModel):
    device_id: str
    mode: str = "exit_zone"
    count: int = 14
    interval: float = 0.7


async def _run_movement(store, broker, req: RunRequest) -> None:
    clat, clng = DEMO_CENTER
    battery = 80.0
    for i in range(req.count):
        if req.mode == "exit_zone":
            # spiral outward so it crosses the fence partway through
            step = 18.0 * i
            lat, lng = _offset(clat, clng, step * math.cos(0.8), step * math.sin(0.8))
        else:
            lat, lng = _offset(clat, clng, 12 * math.sin(i / 2), 12 * math.cos(i / 2))
        p = LocationPoint(
            seq=next(_seq), ts=int(time.time()), lat=round(lat, 6), lng=round(lng, 6),
            accuracy_m=9.0, source=Source.simulator,
            battery_pct=int(round(battery)), motion_state="moving",
        )
        ingest_location(store, broker, req.device_id, p)
        battery = max(0.0, battery - 0.7)
        await asyncio.sleep(req.interval)


@router.post("/demo/run")
async def run(req: RunRequest, store=Depends(get_store), broker=Depends(get_broker)):
    asyncio.create_task(_run_movement(store, broker, req))
    return {"ok": True, "points": req.count}
