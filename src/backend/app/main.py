import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.database import engine
from app.middleware import RequestLoggingMiddleware, configure_logging
from app.middleware.security import SecurityHeadersMiddleware
from app.models import (  # noqa: F401 — ensure models are registered
    Auction,
    AuctionEvent,
    SyncLog,
)

configure_logging(settings.log_level)
logger = structlog.get_logger("pgo-api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Startup
    logger.info("startup", message="Database engine initialised")

    # Start APScheduler if enabled
    scheduler = None
    if settings.sync_enabled:
        try:
            from apscheduler.schedulers.asyncio import (  # type: ignore[import-untyped]
                AsyncIOScheduler,
            )

            from app.services.sync import SyncService

            scheduler = AsyncIOScheduler()
            sync_service = SyncService()
            scheduler.add_job(
                sync_service.run_daily,
                "cron",
                hour=settings.sync_schedule_hour,
                minute=settings.sync_schedule_minute,
                id="daily_sync",
                name="Daily EEX sync",
                replace_existing=True,
            )
            scheduler.start()
            logger.info(
                "scheduler_started",
                hour=settings.sync_schedule_hour,
                minute=settings.sync_schedule_minute,
            )
        except Exception as exc:
            logger.warning("scheduler_failed_to_start", error=str(exc))

    yield

    # Shutdown
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
    await engine.dispose()
    logger.info("shutdown", message="Engine disposed")


app = FastAPI(
    title="French PGO Auctions Dashboard API",
    description="REST API for French Power Guarantees of Origin auction data.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Security headers (outermost middleware — applied last, so headers always set)
app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# API routes
app.include_router(api_router)


def main() -> None:
    pid = os.getpid()
    print(f"[PGO-API] running on port {settings.port} (PID: {pid})")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        workers=1,  # IMPORTANT: keep 1 worker when SYNC_ENABLED=true
        log_config=None,  # suppress uvicorn's default logging; structlog handles it
    )


if __name__ == "__main__":
    main()
