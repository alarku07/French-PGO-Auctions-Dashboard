import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON output."""
    import logging

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every API request with structured JSON fields per Constitution V."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = structlog.get_logger("api.request")

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        self._logger.info(
            "request",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-Id"] = request_id
        return response
