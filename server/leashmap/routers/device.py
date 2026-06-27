"""Device ingestion endpoints. See docs/api/device-protocol.md."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..deps import device_auth, get_broker, get_store
from ..schemas import (
    Command,
    DeviceEvent,
    Heartbeat,
    IngestResponse,
    LocationBatchUpload,
    LocationUpload,
)
from ..services import ingest_location, process_heartbeat
from ..store import to_iso, utcnow

router = APIRouter(prefix="/v1/device", tags=["device"])


def _commands(store, device_id: str) -> List[Command]:
    pending = store.pending_commands.pop(device_id, [])
    return [Command(**c) for c in pending]


def _resp(store, device_id: str, accepted: int, duplicated: int = 0) -> IngestResponse:
    return IngestResponse(
        accepted=accepted,
        duplicated=duplicated,
        server_ts=to_iso(utcnow()),
        commands=_commands(store, device_id),
    )


@router.post("/locations", response_model=IngestResponse)
def upload_location(
    body: LocationUpload,
    _token: str = Depends(device_auth),
    store=Depends(get_store),
    broker=Depends(get_broker),
):
    result = ingest_location(store, broker, body.device_id, body)
    accepted = 1 if result == "accepted" else 0
    return _resp(store, body.device_id, accepted, 1 - accepted)


@router.post("/locations/batch", response_model=IngestResponse)
def upload_batch(
    body: LocationBatchUpload,
    _token: str = Depends(device_auth),
    store=Depends(get_store),
    broker=Depends(get_broker),
):
    accepted = duplicated = 0
    for p in sorted(body.points, key=lambda x: x.ts):
        if ingest_location(store, broker, body.device_id, p) == "accepted":
            accepted += 1
        else:
            duplicated += 1
    return _resp(store, body.device_id, accepted, duplicated)


@router.post("/heartbeat", response_model=IngestResponse)
def heartbeat(
    body: Heartbeat,
    _token: str = Depends(device_auth),
    store=Depends(get_store),
    broker=Depends(get_broker),
):
    process_heartbeat(store, broker, body.device_id, body.mode.value, body.battery_pct)
    return _resp(store, body.device_id, accepted=0)


@router.post("/events", response_model=IngestResponse)
def event(
    body: DeviceEvent,
    _token: str = Depends(device_auth),
    store=Depends(get_store),
    broker=Depends(get_broker),
):
    battery = None
    if body.data and isinstance(body.data.get("battery_pct"), int):
        battery = body.data["battery_pct"]
    store.touch_device(body.device_id, battery_pct=battery)
    return _resp(store, body.device_id, accepted=0)
