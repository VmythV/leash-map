"""Shared dependencies: auth + singletons."""
from __future__ import annotations

from typing import Optional

from fastapi import Header

from .config import settings
from .errors import APIError
from .schemas import User
from .store import Store, store
from .broker import Broker, broker


def get_store() -> Store:
    return store


def get_broker() -> Broker:
    return broker


def _bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise APIError("unauthenticated", "Missing bearer token")
    token = authorization[7:].strip()
    if not token:
        raise APIError("unauthenticated", "Empty bearer token")
    return token


def device_auth(authorization: Optional[str] = Header(default=None)) -> str:
    """Validate the device bearer token. Returns the token.

    In local mode any non-empty token is accepted. If LEASHMAP_DEVICE_TOKEN is
    configured, the token must match exactly.
    """
    token = _bearer(authorization)
    if settings.device_token is not None and token != settings.device_token:
        raise APIError("unauthenticated", "Invalid device token")
    return token


def app_auth(authorization: Optional[str] = Header(default=None)) -> User:
    """Resolve the App session token to a user."""
    token = _bearer(authorization)
    user = store.user_for_session(token)
    if user is None:
        raise APIError("unauthenticated", "Invalid or expired session")
    return user
