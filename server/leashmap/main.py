"""FastAPI application factory."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .broker import broker
from .config import settings
from .errors import install_error_handlers
from .ids import gen_id
from .metrics import metrics
from .routers import alerts, auth, demo, device, geofence, location, pets, realtime
from .services import scan_offline
from .store import store

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
log = logging.getLogger("leashmap.request")


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

    @app.middleware("http")
    async def request_logger(request: Request, call_next):
        request_id = gen_id("req", 6)
        request.state.request_id = request_id
        start = time.perf_counter()
        metrics.inc("http_requests")
        response = await call_next(request)
        dur_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        log.info(
            "%s %s %s %sms rid=%s",
            request.method, request.url.path, response.status_code, dur_ms, request_id,
        )
        return response

    install_error_handlers(app)

    for module in (auth, device, pets, location, geofence, alerts, realtime):
        app.include_router(module.router)
    if settings.app_env == "local":
        app.include_router(demo.router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "env": settings.app_env}

    @app.get("/metrics", tags=["meta"])
    def metrics_endpoint():
        snap = metrics.snapshot()
        snap["sse_subscribers"] = broker.subscriber_count()
        return snap

    return app


app = create_app()
