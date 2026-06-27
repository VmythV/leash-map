"""Alerts."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ..deps import app_auth, get_store
from ..errors import APIError
from ..schemas import Alert, User
from ..store import AlertRecord, to_iso, utcnow

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


def _to_alert(a: AlertRecord) -> Alert:
    return Alert(
        id=a.id,
        pet_id=a.pet_id,
        device_id=a.device_id,
        type=a.type,
        severity=a.severity,
        status=a.status,
        message=a.message,
        location_point_id=a.location_point_id,
        created_at=to_iso(a.created_at),
        acknowledged_at=to_iso(a.acknowledged_at) if a.acknowledged_at else None,
    )


@router.get("")
def list_alerts(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    user: User = Depends(app_auth),
    store=Depends(get_store),
):
    rows = store.alerts_for_owner(user.id, status)[:limit]
    data: List[Alert] = [_to_alert(a) for a in rows]
    return {"data": data, "page": {"next_cursor": None}}


@router.post("/{alert_id}/ack", response_model=Alert)
def ack_alert(alert_id: str, user: User = Depends(app_auth), store=Depends(get_store)):
    a = store.find_alert(alert_id)
    if a is None or a.user_id != user.id:
        raise APIError("not_found", "Alert not found")
    if a.status == "open":
        a = store.set_alert_status(alert_id, "acknowledged", acknowledged_at=utcnow())
    return _to_alert(a)
