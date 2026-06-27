"""App session. See docs/api/README.md."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_store
from ..schemas import DemoSessionRequest, DemoSessionResponse

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/demo-session", response_model=DemoSessionResponse)
def demo_session(body: DemoSessionRequest = DemoSessionRequest(), store=Depends(get_store)):
    user, token = store.create_demo_user(body.display_name)
    return DemoSessionResponse(token=token, user=user)
