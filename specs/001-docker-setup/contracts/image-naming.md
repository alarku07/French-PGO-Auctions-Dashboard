# Contract: Container Image Naming & Tagging

**Branch**: `001-docker-setup` | **Date**: 2026-02-28

---

## Image Naming Convention

```
ghcr.io/<github-owner>/<service-name>:<version>
```

| Service | Image Name |
|---------|-----------|
| Backend | `ghcr.io/<owner>/pgo-auctions-backend:<version>` |
| Frontend | `ghcr.io/<owner>/pgo-auctions-frontend:<version>` |

`<owner>` is the GitHub organization or user that owns the repository.

## Version Tag Strategy

| Tag | Format | Source | Use Case |
|-----|--------|--------|----------|
| Git SHA (default) | `abc1234` (7 chars) | `git rev-parse --short HEAD` | Every build |
| Semantic version | `v1.2.3` | Manual override via `VERSION=` | Release builds |
| `latest` | `latest` | Auto-applied alongside version tag | Points to most recent push |

## Build Argument Contract

Both Dockerfiles accept these build arguments:

| `ARG` | Description | Default |
|-------|-------------|---------|
| `VERSION` | Version identifier baked into image metadata | `dev` |
| `BUILD_DATE` | ISO 8601 timestamp of build | *(unset)* |

## Makefile Variables

The `Makefile` at project root exposes these overridable variables:

| Variable | Default | Override Example |
|----------|---------|-----------------|
| `REGISTRY` | `ghcr.io` | `REGISTRY=docker.io make push` |
| `ORG` | *(from git remote)* | `ORG=myorg make push` |
| `VERSION` | `$(git rev-parse --short HEAD)` | `VERSION=v1.0.0 make push` |
| `SERVICE` | `all` (builds both) | `SERVICE=backend make build` |
