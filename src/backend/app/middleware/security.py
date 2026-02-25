from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

_SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "connect-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "font-src 'self'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

# Cache-Control by path prefix (most-specific first)
_CACHE_RULES: list[tuple[str, str]] = [
    ("/api/v1/health", "no-store"),
    ("/api/v1/regions", "public, max-age=86400"),
    ("/api/v1/technologies", "public, max-age=86400"),
    ("/api/v1/stats", "public, max-age=3600"),
    ("/api/v1/charts/", "public, max-age=3600"),
    ("/api/v1/auctions", "public, max-age=300"),
]


def _cache_control_for(path: str) -> str:
    for prefix, value in _CACHE_RULES:
        if path.startswith(prefix):
            return value
    return "no-cache"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        response: Response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        response.headers["Cache-Control"] = _cache_control_for(request.url.path)
        return response
