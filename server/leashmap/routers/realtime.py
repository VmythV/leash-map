"""SSE realtime stream. See docs/api/realtime-events.md."""
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Request
from sse_starlette.sse import EventSourceResponse

from ..deps import get_broker, get_store
from ..errors import APIError

router = APIRouter(prefix="/v1/realtime", tags=["realtime"])


def _resolve_user(store, authorization: Optional[str], access_token: Optional[str]):
    """SSE auth: EventSource cannot set headers, so a token query param is
    accepted in addition to the Authorization header."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    token = token or access_token
    if not token:
        raise APIError("unauthenticated", "Missing token")
    user = store.user_for_session(token)
    if user is None:
        raise APIError("unauthenticated", "Invalid or expired session")
    return user


@router.get("/stream")
async def stream(
    request: Request,
    pet_id: Optional[str] = Query(default=None),
    access_token: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
    store=Depends(get_store),
    broker=Depends(get_broker),
):
    user = _resolve_user(store, authorization, access_token)
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
