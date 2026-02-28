# Contract: Reverse Proxy Routing

**Branch**: `001-docker-setup` | **Date**: 2026-02-28

---

## Overview

The reverse proxy (`nginx-proxy`) is the sole entry point exposed to the host. All browser traffic enters through port 80 and is routed internally by path prefix.

## Routing Rules

| Priority | Path Pattern | Routes To | Notes |
|----------|-------------|-----------|-------|
| 1 | `/api/*` | `backend:8000` | All FastAPI endpoints (existing prefix from `app/main.py`) |
| 2 | `/*` | `frontend:80` | Vue SPA static files (production) or Vite dev server (dev) |

## Health Check Routing

| Path | Handled By | Response |
|------|-----------|----------|
| `/health` | nginx-proxy (internal) | `200 OK` — nginx itself responds, not proxied |

## WebSocket Routing (Dev Mode Only)

| Path | Routes To | Purpose |
|------|-----------|---------|
| `/*` with `Upgrade: websocket` header | `frontend:5173` | Vite HMR WebSocket connection |

## Port Exposure Contract

| Service | Internal Port | Host Port (prod) | Host Port (dev) |
|---------|--------------|-----------------|----------------|
| `nginx-proxy` | 80 | **80** | **80** |
| `frontend` | 80 (prod) / 5173 (dev) | *(none)* | *(none)* |
| `backend` | 8000 | *(none)* | *(none)* |
| `postgres` | 5432 | *(none)* | *(none, or 5432 dev override)* |

No backend, frontend, or database ports are exposed to the host in production mode.

## CORS Contract

Since all browser requests originate from the same host origin (`http://localhost`), the FastAPI CORS middleware must allow `http://localhost` only. No wildcard origins. The backend's existing CORS configuration (`CORS_ORIGINS` env var) must be updated to reflect the proxied origin.
