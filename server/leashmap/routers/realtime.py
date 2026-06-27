"""SSE realtime stream. See docs/api/realtime-events.md."""
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sse_starlette.sse import EventSourceResponse

from ..deps import app_auth, get_broker
from ..schemas import User

router = APIRouter(prefix="/v1/realtime", tags=["realtime"])


@router.get("/stream")
async def stream(
    request: Request,
    pet_id: Optional[str] = Query(default=None),
    user: User = Depends(app_auth),
    broker=Depends(get_broker),
):
    queue = broker.subscribe(user.id)

    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    continue  # EventSourceResponse emits keepalive pings
                data = msg["data"]
                if pet_id and data.get("pet_id") not in (None, pet_id):
                    continue
                yield {"event": msg["event"], "data": json.dumps(data, ensure_ascii=False)}
        finally:
            broker.unsubscribe(user.id, queue)

    return EventSourceResponse(gen(), ping=15)
