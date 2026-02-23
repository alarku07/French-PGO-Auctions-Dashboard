<!--
  SYNC IMPACT REPORT
  ==================
  Version change: N/A → 1.0.0 (initial ratification — filled from blank template)

  Modified principles: None (new document; no prior principles existed)

  Added sections:
    - Core Principles (I. Data Integrity, II. Quality Gates, III. Python Discipline,
      IV. Frontend Standards, V. Observability)
    - Technology Stack Constraints
    - Development Workflow
    - Governance

  Removed sections: None

  Templates requiring updates:
    ✅ .specify/templates/plan-template.md — Constitution Check gates now derivable
       from V1.0.0 principles; no structural change to template required.
    ✅ .specify/templates/spec-template.md — Aligns with V1.0.0 scope and quality
       requirements; no structural changes required.
    ✅ .specify/templates/tasks-template.md — Task categories (Setup, Foundational,
       User Story phases) align with Quality Gates and Data Integrity principles;
       no structural changes required.
    ✅ .specify/templates/agent-file-template.md — Technology-agnostic; no updates needed.
    ✅ .specify/templates/checklist-template.md — Feature-agnostic; no updates needed.
    ✅ .claude/commands/*.md — No outdated or agent-specific principle references found.

  Deferred TODOs: None — all placeholders resolved.
-->

# French PGO Auctions Dashboard Constitution

## Core Principles

### I. Data Integrity (NON-NEGOTIABLE)

Live data MUST never be deleted. Database selection MUST follow project policy:

- **PostgreSQL** MUST be used for all production and active development environments.
- **SQLite** is permitted ONLY for proof-of-concept work or quick local mock-ups, never
  as a substitute for production-grade storage.
- Any migration that drops rows, tables, or columns on a live dataset MUST receive
  explicit, documented operator approval before execution.
- Destructive SQL operations (`DROP`, `TRUNCATE`, mass `DELETE`) against live data are
  prohibited without a written rollback plan reviewed by at least one peer.

**Rationale**: Auction records carry legal and financial weight. Irreversible data loss can
produce regulatory or contractual liability. Defense-in-depth at the data layer is mandatory.

### II. Quality Gates (NON-NEGOTIABLE)

All three gates MUST be green before any commit is accepted or any task is marked complete:

1. **Linting** — zero lint errors (backend: `flake8` or `ruff`; frontend: ESLint).
2. **Type checking** — zero type errors (backend: `mypy`; frontend: strict TypeScript
   where applicable).
3. **Unit tests** — full suite passes with no unexplained failures or skips.

Pull requests MUST NOT be merged until all three gates pass. Bypass flags such as
`--no-verify` or `--skip-checks` are prohibited unless a documented emergency exception
is approved and immediately followed by a remediation ticket.

**Rationale**: Consistent enforcement prevents regressions and keeps the codebase
maintainable as complexity grows.

### III. Python Discipline

All backend Python development MUST adhere to the following rules:

- **Virtual environment**: The `.venv` virtual environment MUST always be active. Packages
  MUST NOT be installed into the global Python interpreter. If a venv cannot be used (e.g.,
  inside a Docker image build), the team MUST be consulted and the decision documented
  before any installation proceeds.
- **Ignored path**: The `.venv/` directory MUST be excluded from version control and
  ignored by all tooling (linters, type checkers, file watchers).
- **Code style**: PEP 8 compliance is mandatory. Double quotes MUST be used for all
  string literals — single quotes are not permitted.
- **Async-first**: Async-friendly libraries (e.g., `asyncio`, `httpx`, `aiofiles`,
  `SQLAlchemy` async engine) MUST be preferred. Synchronous-only libraries are permitted
  only when no viable async alternative exists; the decision MUST be documented in the
  relevant plan or PR description.
- **Latest stable Python**: The backend MUST target the latest stable Python release.
  Pinned versions MUST be recorded in a `requirements.txt` or `pyproject.toml`.

**Rationale**: Consistent Python conventions reduce onboarding friction, prevent
environment-sourced bugs, and ensure the async backend can handle concurrent auction
workloads efficiently.

### IV. Frontend Standards

The Vue.js frontend MUST comply with the following standards:

- **Framework**: Latest stable Vue.js release. Use Composition API. Upgrades MUST be tested against the full
  suite before merging.
- **Responsive & mobile-friendly**: Every page MUST render correctly on viewport widths
  from 320 px to 1920 px. Mobile breakpoints are a hard requirement, not optional polish.
- **Component architecture**: Business logic MUST NOT live in template blocks. Logic
  belongs in composables, stores, or service modules.
- **Linting**: ESLint MUST pass with zero errors before any commit (see Principle II).
- **Accessibility**: Interactive elements MUST be keyboard-navigable and carry appropriate
  ARIA attributes.

**Rationale**: Auction participants access the dashboard from diverse devices, including
mobile phones at auction sites. Mobile support is a core functional requirement.

### V. Observability

All local services started during development MUST print the following line to stdout
immediately upon startup:

```
[SERVICE NAME] running on port [PORT] (PID: [PID])
```

The backend API MUST implement structured logging for every endpoint. Each log entry MUST
include at minimum: timestamp (ISO 8601), request ID, endpoint path, HTTP method, response
status code, and request duration in milliseconds.

**Rationale**: Clear runtime feedback dramatically reduces debugging time. Structured logs
enable future integration with log aggregation tools without code changes.

## Technology Stack Constraints

The following stack is authoritative for this project. Any deviation MUST be proposed as a
constitution amendment before work begins.

| Layer       | Technology                          | Notes                                        |
|-------------|-------------------------------------|----------------------------------------------|
| Backend     | Python (latest stable)              | Async-friendly libraries preferred           |
| Frontend    | Vue.js (latest stable)              | Responsive, mobile-first                     |
| DB (prod)   | PostgreSQL                          | Required for all non-POC environments        |
| DB (POC)    | SQLite                              | Permitted only for mock-ups and local spikes |
| Backend tests | pytest                            | Async test support via `pytest-asyncio`      |
| Frontend tests | Vitest (or Vue Test Utils)       | Component and integration testing            |

### Source Layout

```
src/
  backend/    # Python backend
  frontend/   # Vue.js frontend
tests/        # Test suite
docs/         # Documentation
```

## Development Workflow

1. **Branch**: Create a feature branch per spec using the `###-feature-name` naming
   convention before writing any implementation code.
2. **Spec first**: A feature MUST have an approved spec under `.specify/specs/` before
   implementation begins. The plan MUST pass its Constitution Check before Phase 0 research.
3. **Quality Gates**: Run lint, type check, and unit tests locally before every commit
   (Principle II). Do not rely on CI to catch what local checks can prevent.
4. **Service startup output**: Follow the Principle V format whenever starting a local
   service during development.
5. **Data-touching tasks**: Any task that modifies, migrates, or deletes data MUST be
   reviewed against Principle I before the PR is approved.
6. **PR checklist**: All PRs MUST reference their associated spec and confirm all Quality
   Gates are green. The plan's Constitution Check section documents feature-specific gates.

## Governance

This constitution supersedes all other development practices, informal conventions, README
instructions, and ticket-level guidance. Any conflicting rule MUST be resolved by amending
this document — not by ignoring it.

**Amendment Procedure**:
1. Propose the change as a pull request that modifies `.specify/memory/constitution.md`.
2. Increment the version number following the policy below.
3. Update the Sync Impact Report HTML comment at the top of the file to reflect all changes.
4. Propagate amendments to any affected templates or command files and mark them in the report.
5. Obtain at least one peer review approval before merging.

**Versioning Policy**:
- **MAJOR**: Backward-incompatible principle removal, redefinition that changes enforcement,
  or fundamental governance restructuring.
- **MINOR**: New principle or section added, or materially expanded guidance in an existing
  principle.
- **PATCH**: Clarifications, wording improvements, typo fixes, or non-semantic refinements.

**Compliance Review**: Every PR review MUST verify that the changes comply with this
constitution. The Constitution Check section in each feature's `plan.md` enumerates the
active gates applicable to that feature.

**Version**: 1.0.0 | **Ratified**: 2026-02-23 | **Last Amended**: 2026-02-23
