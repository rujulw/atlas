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

## 4. Auth guard dependency for protected route access
- Status: accepted
- Area: backend
- Decision: enforce JWT bearer token validation through a reusable dependency and apply it to protected routes.
- Context: once JWT issuance exists, API endpoints need a shared enforcement path to prevent route-by-route auth drift.
- Options considered:
  - Option A: inline token checks in each protected route
  - Option B: dependency-based guard using a shared token verification service
- Tradeoffs:
  - Pros:
    - Single validation path for signature, expiry, and subject checks
    - Clear 401 behavior contract (`WWW-Authenticate: Bearer`) for clients
  - Cons:
    - Slight indirection when reading route handlers
- Outcome: `/api/v1/auth/me` now requires bearer auth and returns authenticated subject identity.
- Follow-up actions:
  - Add route guard coverage to integration tests across register/login/protected failures
  - Introduce user lookup in guard once login is backed by persisted credentials
- References: `server/app/api/routes/auth.py`, `server/app/services/auth.py`, `server/tests/api/v1/test_auth.py`

## 5. File metadata schema and storage constraints baseline
- Status: accepted
- Area: backend
- Decision: define a metadata-first `files` schema plus strict storage path and ownership constraints before implementing upload/download endpoints.
- Context: storage APIs need an explicit contract for path generation, ownership checks, and integrity metadata to avoid implicit behavior changes across later commits.
- Options considered:
  - Option A: implement upload/download first and derive schema from endpoint behavior
  - Option B: define schema and constraints first, then implement endpoints against that contract
- Tradeoffs:
  - Pros:
    - Reduces migration churn by agreeing on table fields and constraints early
    - Prevents path traversal and ownership bugs caused by ad-hoc storage keys
  - Cons:
    - Requires upfront modeling work before visible API features land
- Outcome: v1 storage design now specifies `files` metadata columns (`owner_id`, `storage_key`, `size_bytes`, `checksum_sha256`, timestamps, soft-delete) and enforcement constraints (owner-scoped access, server-generated keys, root-scoped disk access).
- Follow-up actions:
  - Add SQLAlchemy `File` model and Alembic migration
  - Introduce storage service interfaces for key generation, write/read, and metadata persistence
  - Add API tests for upload/download ownership and invalid-path access
- References: `docs/architecture.md`, `server/app/models/user.py`, `commits.txt`

## 6. File model + migration + storage interface boundary
- Status: accepted
- Area: backend
- Decision: implement a concrete `files` metadata table and introduce storage service protocols before endpoint logic.
- Context: upload/download endpoints require a stable persistence layer and storage abstraction to avoid coupling route code to filesystem details.
- Options considered:
  - Option A: implement storage endpoints first with inline filesystem code
  - Option B: land model/migration/contracts first, then build endpoints on top
- Tradeoffs:
  - Pros:
    - Ensures Alembic/database state is ready before API wiring
    - Gives upload/download implementation a testable service seam
  - Cons:
    - Adds one intermediate commit before feature-visible endpoint behavior
- Outcome: `File` model and `20260305_0003_create_files` migration added; storage contracts defined via `StorageKeyService`, `BlobStorageService`, and `StoredFileObject`.
- Follow-up actions:
  - Implement concrete local-disk storage service with safe key generation
  - Add upload endpoint that writes bytes and persists metadata rows
  - Add ownership checks for download access path
- References: `server/app/models/file.py`, `server/migrations/versions/20260305_0003_create_files.py`, `server/app/services/storage.py`
