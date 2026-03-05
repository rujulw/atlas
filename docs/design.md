# Design Log

## 1. API versioned routing baseline
- Status: accepted
- Area: backend
- Decision: Introduce `/api/v1/*` route namespace from the first endpoint implementation.
- Context: Early versioning prevents future breaking changes from leaking into unversioned paths.
- Options considered:
  - Option A: Unversioned API paths
  - Option B: Versioned API paths from the start
- Tradeoffs:
  - Pros:
    - Clean contract for private instance repos
    - Easier future `v2` introduction
  - Cons:
    - Slightly longer route paths
- Outcome: Health endpoint ships at `/api/v1/health`.
- Follow-up actions:
  - Add route-level tests per endpoint module
  - Document API conventions in docs when auth routes are added
- References: `server/app/api/router.py`, `server/app/api/v1/router.py`, `server/app/api/routes/health.py`

## 2. Containerized development baseline
- Status: accepted
- Area: infra
- Decision: standardize local development on Docker Compose with db/server/client services.
- Context: contributors need a reproducible, low-friction environment across machines.
- Options considered:
  - Option A: host-only processes via language-specific package managers
  - Option B: compose-managed local stack
- Tradeoffs:
  - Pros:
    - Reproducible boot path for public contributors
    - Consistent runtime diagnostics with shared commands
  - Cons:
    - Slightly slower startup due container/image lifecycle
- Outcome: `docker/docker-compose.yml` + `make docker-*` commands added.
- Follow-up actions:
  - Add service-specific health checks for frontend and backend containers
  - Add CI smoke test for compose boot
- References: `docker/docker-compose.yml`, `Makefile`, `docker/server.Dockerfile`, `docker/client.Dockerfile`

## 3. Auth-first API contract with stub token service
- Status: accepted
- Area: backend
- Decision: expose `/api/v1/auth/login` and `/api/v1/auth/register` early using stubbed token issuance.
- Context: frontend and private instance repos need stable API contracts before full auth internals exist.
- Options considered:
  - Option A: defer auth routes until complete implementation
  - Option B: ship route contracts with explicit stubs
- Tradeoffs:
  - Pros:
    - Enables frontend/API integration in parallel
    - Makes implementation gaps explicit and trackable
  - Cons:
    - Temporary behavior can be mistaken for production-ready auth
- Outcome: login returns a stub access token; register returns `501` until implemented.
- Follow-up actions:
  - Replace stub token service with signed JWT implementation
  - Add persistence and password hashing flow
- References: `server/app/api/routes/auth.py`, `server/app/services/auth.py`, `server/app/schemas/auth.py`
