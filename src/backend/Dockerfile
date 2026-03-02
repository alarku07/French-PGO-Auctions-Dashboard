# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY app/ app/

RUN pip install --no-cache-dir .

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS runtime

# Install postgresql-client for pg_isready in entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 10001 appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app

# Copy application source and entrypoint with correct ownership
COPY --chown=appuser:appuser app/ app/
COPY --chown=appuser:appuser alembic/ alembic/
COPY --chown=appuser:appuser alembic.ini .
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

# Pre-create the downloads cache directory with correct ownership
RUN mkdir -p /app/data/downloads && chown -R appuser:appuser /app/data

ENV PYTHONUNBUFFERED=1

ARG VERSION=dev
ARG BUILD_DATE

USER appuser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
