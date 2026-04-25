from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, auth, events, items, jobs
from app.core.config import get_settings
from app.db.database import init_db
from app.services import start_queue_worker, stop_queue_worker


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(items.router, prefix="/api/items", tags=["items"])
    app.include_router(events.router, prefix="/api", tags=["events"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()
        start_queue_worker(settings)

    @app.on_event("shutdown")
    def on_shutdown() -> None:
        stop_queue_worker()

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
