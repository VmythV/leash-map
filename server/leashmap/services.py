"""Domain processing: ingestion pipeline, geofence + alert evaluation.

Kept transport-agnostic so routers stay thin. See docs/api/device-protocol.md
and docs/api/realtime-events.md.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .broker import Broker
from .config import settings
from .geo import haversine_m
from .metrics import metrics
from .notifications import notifier
from .schemas import LocationPoint
from .store import AlertRecord, LocationRecord, PetSettingsRecord, Store, to_iso, utcnow


def _hour_in_window(hour: int, start: Optional[int], end: Optional[int]) -> bool:
    """True if `hour` falls in [start, end) (UTC), handling overnight wrap."""
    if start is None or end is None:
        return False
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end  # overnight


def _in_quiet_hours(st: PetSettingsRecord, now: datetime) -> bool:
    return _hour_in_window(now.hour, st.quiet_start, st.quiet_end)


def _within_active_window(start: Optional[int], end: Optional[int], now: datetime) -> bool:
    if start is None or end is None:
        return True
    return _hour_in_window(now.hour, start, end)


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
    deliver: bool = True,
) -> AlertRecord:
    alert = store.create_alert(
        user_id=user_id, pet_id=pet_id, device_id=device_id, type_=type_,
        severity=severity, message=message, location_point_id=location_point_id,
    )
    # Always pushed to the App in real time; quiet hours only suppress
    # out-of-band delivery (push/SMS).
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
    notifier.dispatch(store, alert, deliver=deliver)
    metrics.inc("alerts_created")
    metrics.inc(f"alerts_created_{type_}")
    return alert


def _eval_geofences(store: Store, broker: Broker, rec: LocationRecord, owner_id: str,
                    pet_name: str, st: PetSettingsRecord) -> None:
    if rec.accuracy_m > settings.geofence_accuracy_threshold_m:
        return  # ignore low-accuracy points for geofencing (avoid false alarms)
    now = utcnow()
    quiet = _in_quiet_hours(st, now)
    for gf in store.geofences_for_pet(rec.pet_id):
        if not gf.enabled or not _within_active_window(gf.active_start, gf.active_end, now):
            continue
        inside = haversine_m(rec.lat, rec.lng, gf.center_lat, gf.center_lng) <= gf.radius_m

        if inside:
            # entering from outside -> home alert
            if gf.last_inside is False and gf.alert_on_enter and st.enter_enabled:
                _create_alert(
                    store, broker, user_id=owner_id, pet_id=rec.pet_id, device_id=rec.device_id,
                    type_="enter_zone", severity="info",
                    message=f"{pet_name} 已回到安全区域「{gf.name}」",
                    location_point_id=rec.id, deliver=not quiet,
                )
            if gf.open_alert_id:
                store.set_alert_status(gf.open_alert_id, "resolved")
            store.update_geofence_state(gf.id, 0, None, last_inside=True)
        else:
            consecutive = gf.consecutive_outside + 1
            open_alert_id = gf.open_alert_id
            if (consecutive >= settings.geofence_exit_consecutive and open_alert_id is None
                    and gf.alert_on_exit and st.exit_enabled):
                alert = _create_alert(
                    store, broker, user_id=owner_id, pet_id=rec.pet_id, device_id=rec.device_id,
                    type_="exit_zone", severity="warning",
                    message=f"{pet_name} 可能离开了安全区域「{gf.name}」",
                    location_point_id=rec.id, deliver=not quiet,
                )
                open_alert_id = alert.id
            store.update_geofence_state(gf.id, consecutive, open_alert_id, last_inside=False)


def _eval_battery(store: Store, broker: Broker, rec: LocationRecord, owner_id: str,
                  pet_name: str, st: PetSettingsRecord) -> None:
    if rec.battery_pct is None or not st.low_battery_enabled:
        return
    threshold = st.low_battery_threshold if st.low_battery_threshold is not None else settings.low_battery_threshold
    existing = store.open_alert(rec.pet_id, "low_battery")
    if rec.battery_pct <= threshold and existing is None:
        _create_alert(
            store, broker, user_id=owner_id, pet_id=rec.pet_id, device_id=rec.device_id,
            type_="low_battery", severity="warning",
            message=f"{pet_name} 的设备电量低（{rec.battery_pct}%），请尽快充电",
            location_point_id=rec.id, deliver=not _in_quiet_hours(st, utcnow()),
        )
    elif rec.battery_pct > threshold and existing is not None:
        store.set_alert_status(existing.id, "resolved")


def _quality_reject_reason(store: Store, device_id: str, pet_id: Optional[str], p: LocationPoint) -> Optional[str]:
    """Return a reason string if the point should be rejected, else None."""
    now = int(utcnow().timestamp())
    if p.ts <= 0 or abs(now - p.ts) > settings.max_ts_drift_seconds:
        return "ts_drift"
    if pet_id:
        prev = store.latest_for_pet(pet_id)
        if prev is not None and p.ts > prev.ts:
            dt = p.ts - prev.ts
            dist = haversine_m(prev.lat, prev.lng, p.lat, p.lng)
            if dt > 0 and dist / dt > settings.max_speed_mps:
                return "speed_jump"
    return None


def ingest_location(store: Store, broker: Broker, device_id: str, p: LocationPoint) -> str:
    """Process one location point. Returns 'accepted', 'duplicate', or 'rejected'."""
    if store.is_duplicate(device_id, p.seq):
        metrics.inc("locations_duplicate")
        return "duplicate"

    pet_id = store.pet_for_device(device_id)

    settings_rec = store.get_pet_settings(pet_id) if pet_id else None
    if settings_rec is not None and settings_rec.tracking_paused:
        # privacy pause: drop the point entirely (no storage, no alerts)
        metrics.inc("locations_paused")
        return "rejected"

    reason = _quality_reject_reason(store, device_id, pet_id, p)
    if reason is not None:
        metrics.inc("locations_rejected")
        metrics.inc(f"locations_rejected_{reason}")
        return "rejected"

    rec = store.add_location(device_id, pet_id, p)
    metrics.inc("locations_accepted")
    st = store.touch_device(device_id, battery_pct=p.battery_pct)

    if pet_id:
        pet = store.get_pet(pet_id)
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
        _eval_geofences(store, broker, rec, pet.owner_id, pet.name, settings_rec)
        _eval_battery(store, broker, rec, pet.owner_id, pet.name, settings_rec)

    return "accepted"


def scan_offline(store: Store, broker: Broker, now: Optional[datetime] = None) -> int:
    """Raise/resolve offline alerts by comparing last_seen against the threshold.

    Returns the number of new offline alerts created. Pure enough to unit-test
    by seeding device_status rows with an old last_seen.
    """
    now = now or utcnow()
    threshold = timedelta(seconds=settings.offline_threshold_seconds)
    created = 0
    for st in store.all_device_status():
        pet_id = store.pet_for_device(st.device_id)
        if not pet_id:
            continue
        pet = store.get_pet(pet_id)
        if pet is None:
            continue
        prefs = store.get_pet_settings(pet_id)
        if not prefs.offline_enabled:
            continue
        offline = st.last_seen is None or (now - st.last_seen) > threshold
        existing = store.open_alert(pet_id, "offline")
        if offline and existing is None:
            _create_alert(
                store, broker,
                user_id=pet.owner_id, pet_id=pet_id, device_id=st.device_id,
                type_="offline", severity="warning",
                message=f"{pet.name} 的设备已离线，最后在线时间 "
                        f"{to_iso(st.last_seen) if st.last_seen else '未知'}",
                location_point_id=None,
                deliver=not _in_quiet_hours(prefs, now),
            )
            created += 1
        elif not offline and existing is not None:
            store.set_alert_status(existing.id, "resolved")
            broker.publish(pet.owner_id, "device.status_updated", {
                "device_id": st.device_id, "pet_id": pet_id, "online": True,
                "mode": st.mode, "last_seen_at": to_iso(st.last_seen) if st.last_seen else None,
            })
    return created


def process_heartbeat(store: Store, broker: Broker, device_id: str, mode: str, battery_pct: int) -> None:
    st = store.touch_device(device_id, mode=mode, battery_pct=battery_pct)
    pet_id = store.pet_for_device(device_id)
    if pet_id:
        pet = store.get_pet(pet_id)
        broker.publish(pet.owner_id, "device.status_updated", {
            "device_id": device_id,
            "pet_id": pet_id,
            "online": True,
            "mode": st.mode,
            "last_seen_at": to_iso(st.last_seen) if st.last_seen else None,
        })
