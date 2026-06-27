"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .errors import install_error_handlers
from .routers import alerts, auth, device, geofence, location, pets, realtime


def create_app() -> FastAPI:
    app = FastAPI(
        title="LeashMap API",
        version="1.0.0",
        description="LeashMap Cloud MVP. Contract: docs/api/.",
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

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
