"""FastAPI application factory."""
from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .broker import broker
from .config import settings
from .errors import install_error_handlers
from .routers import alerts, auth, demo, device, geofence, location, pets, realtime
from .services import scan_offline
from .store import store


async def _offline_scan_loop() -> None:
    interval = settings.offline_scan_interval_seconds
    while True:
        await asyncio.sleep(interval)
        try:
            scan_offline(store, broker)
        except Exception:  # pragma: no cover - background task must not die
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_offline_scan_loop())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def create_app() -> FastAPI:
    app = FastAPI(
        title="LeashMap API",
        version="1.0.0",
        description="LeashMap Cloud MVP. Contract: docs/api/.",
        lifespan=lifespan,
    )

    # Permissive CORS for local App/dashboard development.
    if settings.app_env == "local":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    install_error_handlers(app)

    for module in (auth, device, pets, location, geofence, alerts, realtime):
        app.include_router(module.router)
    if settings.app_env == "local":
        app.include_router(demo.router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
