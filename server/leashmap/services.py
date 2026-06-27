"""Domain processing: ingestion pipeline, geofence + alert evaluation.

Kept transport-agnostic so routers stay thin. See docs/api/device-protocol.md
and docs/api/realtime-events.md.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .broker import Broker
from .config import settings
from .geo import haversine_m
from .ids import gen_id
from .schemas import LocationPoint
from .store import AlertRecord, GeofenceRecord, LocationRecord, Store, to_iso, utcnow


def _app_location_payload(rec: LocationRecord) -> dict:
    return {
        "ts": to_iso(rec.dt),
        "lat": rec.lat,
        "lng": rec.lng,
        "accuracy_m": rec.accuracy_m,
        "source": rec.source,
        "speed_mps": rec.speed_mps,
        "heading": rec.heading,
        "motion_state": rec.motion_state,
    }


def _create_alert(
    store: Store,
    broker: Broker,
    *,
    user_id: str,
    pet_id: str,
    device_id: Optional[str],
    type_: str,
    severity: str,
    message: str,
    location_point_id: Optional[int],
) -> AlertRecord:
    alert = AlertRecord(
        id=gen_id("alt"),
        user_id=user_id,
        pet_id=pet_id,
        device_id=device_id,
        type=type_,
        severity=severity,
        status="open",
        message=message,
        location_point_id=location_point_id,
        created_at=utcnow(),
    )
    store.add_alert(alert)
    broker.publish(user_id, "alert.created", {
        "alert_id": alert.id,
        "pet_id": pet_id,
        "device_id": device_id,
        "type": type_,
        "severity": severity,
        "status": "open",
        "message": message,
        "created_at": to_iso(alert.created_at),
        "location_point_id": location_point_id,
    })
    return alert


def _eval_geofences(store: Store, broker: Broker, rec: LocationRecord, owner_id: str, pet_name: str) -> None:
    accurate = rec.accuracy_m <= settings.geofence_accuracy_threshold_m
    for gf in store.geofences_for_pet(rec.pet_id):
        if not gf.enabled:
            continue
        state = store.geofence_state[gf.id]
        dist = haversine_m(rec.lat, rec.lng, gf.center_lat, gf.center_lng)
        outside = dist > gf.radius_m
        if outside and accurate:
            state.consecutive_outside += 1
            if (
                state.consecutive_outside >= settings.geofence_exit_consecutive
                and state.open_alert_id is None
            ):
                alert = _create_alert(
                    store, broker,
                    user_id=owner_id, pet_id=rec.pet_id, device_id=rec.device_id,
                    type_="exit_zone", severity="warning",
                    message=f"{pet_name} 可能离开了安全区域「{gf.name}」",
                    location_point_id=rec.id,
                )
                state.open_alert_id = alert.id
        elif not outside:
            state.consecutive_outside = 0
            if state.open_alert_id:
                a = store.find_alert(state.open_alert_id)
                if a and a.status == "open":
                    a.status = "resolved"
                state.open_alert_id = None


def _eval_battery(store: Store, broker: Broker, rec: LocationRecord, owner_id: str, pet_name: str) -> None:
    if rec.battery_pct is None:
        return
    threshold = settings.low_battery_threshold
    existing = store.open_alert(rec.pet_id, "low_battery")
    if rec.battery_pct <= threshold and existing is None:
        _create_alert(
            store, broker,
            user_id=owner_id, pet_id=rec.pet_id, device_id=rec.device_id,
            type_="low_battery", severity="warning",
            message=f"{pet_name} 的设备电量低（{rec.battery_pct}%），请尽快充电",
            location_point_id=rec.id,
        )
    elif rec.battery_pct > threshold and existing is not None:
        existing.status = "resolved"


def ingest_location(store: Store, broker: Broker, device_id: str, p: LocationPoint) -> str:
    """Process one location point. Returns 'accepted' or 'duplicate'."""
    if store.is_duplicate(device_id, p.seq):
        return "duplicate"

    pet_id = store.pet_for_device(device_id)
    rec = LocationRecord(
        id=store.next_location_id(),
        device_id=device_id,
        pet_id=pet_id,
        seq=p.seq,
        ts=p.ts,
        dt=datetime.fromtimestamp(p.ts, tz=timezone.utc),
        lat=p.lat,
        lng=p.lng,
        accuracy_m=p.accuracy_m,
        source=p.source.value,
        speed_mps=p.speed_mps,
        heading=p.heading,
        battery_pct=p.battery_pct,
        motion_state=p.motion_state.value if p.motion_state else None,
    )
    store.add_location(rec)
    st = store.touch_device(device_id, battery_pct=p.battery_pct)

    if pet_id:
        pet = store.pets[pet_id]
        payload = {"pet_id": pet_id, "device_id": device_id}
        payload.update(_app_location_payload(rec))
        broker.publish(pet.owner_id, "location.updated", payload)
        broker.publish(pet.owner_id, "device.battery_updated", {
            "device_id": device_id,
            "pet_id": pet_id,
            "battery_pct": st.battery_pct,
            "charging": False,
            "ts": to_iso(rec.dt),
        })
        _eval_geofences(store, broker, rec, pet.owner_id, pet.name)
        _eval_battery(store, broker, rec, pet.owner_id, pet.name)

    return "accepted"


def process_heartbeat(store: Store, broker: Broker, device_id: str, mode: str, battery_pct: int) -> None:
    st = store.touch_device(device_id, mode=mode, battery_pct=battery_pct)
    pet_id = store.pet_for_device(device_id)
    if pet_id:
        pet = store.pets[pet_id]
        broker.publish(pet.owner_id, "device.status_updated", {
            "device_id": device_id,
            "pet_id": pet_id,
            "online": True,
            "mode": st.mode,
            "last_seen_at": to_iso(st.last_seen) if st.last_seen else None,
        })
