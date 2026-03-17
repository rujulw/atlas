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
- References: `docs/architecture.md`, `docs/roadmap.md`, `server/app/models/user.py`

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

## 7. Upload endpoint with metadata-first persistence
- Status: accepted
- Area: backend
- Decision: implement authenticated multipart upload as a composed flow: resolve authenticated owner -> generate server storage key -> write bytes -> persist file metadata row -> return metadata response.
- Context: upload is the first storage API touching both disk and database, so behavior must preserve ownership and integrity guarantees from prior design commits.
- Options considered:
  - Option A: write bytes in route and inline metadata logic
  - Option B: route orchestration over repository + storage services with explicit response schema
- Tradeoffs:
  - Pros:
    - Keeps endpoint logic thin and service boundaries reusable for download/listing
    - Preserves one source of truth for checksum/size via storage write result
  - Cons:
    - Adds dependency wiring complexity in route module
- Outcome: `/api/v1/files/upload` added with JWT auth enforcement and metadata persistence into `files` table.
- Follow-up actions:
  - Add download endpoint with owner check and storage read path
  - Add list endpoint with owner filter and pagination
  - Add cleanup behavior for DB failure after file write (transactional reconciliation)
- References: `server/app/api/routes/files.py`, `server/app/services/storage.py`, `server/app/repositories/file.py`, `server/app/schemas/file.py`

## 8. Download endpoint with ownership and path-safety enforcement
- Status: accepted
- Area: backend
- Decision: serve downloads only through owner-scoped metadata lookup and validated storage-key reads.
- Context: download is the highest-risk storage read path; ownership checks and path safety must be hard requirements at route boundary.
- Options considered:
  - Option A: direct path-based download endpoint accepting storage key/path input
  - Option B: id-based endpoint resolving metadata by `(file_id, owner_id)` and reading through blob service
- Tradeoffs:
  - Pros:
    - Prevents cross-user file reads by binding lookup to authenticated owner
    - Keeps filesystem access behind storage service path validation
  - Cons:
    - Requires extra metadata query before each file read
- Outcome: `/api/v1/files/{file_id}/download` added with strict owner filter and not-found semantics for missing metadata/content.
- Follow-up actions:
  - Add integration tests for successful download, invalid ownership, and missing blob/content cases
  - Add range/streaming support for large files in future media slice
- References: `server/app/api/routes/files.py`, `server/app/repositories/file.py`, `server/app/services/storage.py`

## 9. Storage API integration coverage baseline
- Status: accepted
- Area: backend
- Decision: enforce integration coverage for upload/download happy paths and ownership/content failure scenarios as a release gate for the storage-metadata branch.
- Context: storage correctness depends on interactions across auth, metadata persistence, and filesystem behavior, which unit tests alone do not sufficiently validate.
- Options considered:
  - Option A: unit-test repositories/services only
  - Option B: add API-level integration tests over an isolated DB + temporary storage root
- Tradeoffs:
  - Pros:
    - Verifies end-to-end behavior for ownership checks and download response contracts
    - Catches metadata/blob drift and missing-content regressions early
  - Cons:
    - Slightly higher test runtime and fixture setup complexity
- Outcome: integration tests now cover upload persistence, owner download success, invalid-owner access (`404`), and missing blob/content (`404`).
- Follow-up actions:
  - Extend storage tests with malformed multipart payload and large-file streaming scenarios
  - Add CI gate for storage integration suite in pull request checks
- References: `server/tests/api/v1/test_files_integration.py`, `server/app/api/routes/files.py`

## 10. Privacy-first auth direction for internal private services
- Status: accepted
- Area: backend
- Decision: evolve Atlas auth into a tailnet-only identity layer using encrypted identity fields, blind indexes, internal user-id token subjects, refresh-token sessions, and explicit service-to-service trust boundaries.
- Context: Atlas is intended to be a private personal-cloud platform rather than a public internet application, and future internal services on the same server should trust Atlas identity instead of reimplementing auth.
- Options considered:
  - Option A: keep plaintext identity fields and email-based JWT subjects for simplicity
  - Option B: move toward encrypted identity storage, blind-index lookup, user-id subjects, and revocable session-backed auth
- Tradeoffs:
  - Pros:
    - Reduces user identity exposure if the database is compromised
    - Gives future private subservices a stable trust anchor independent of mutable email addresses
    - Supports device-aware revocation and a more production-sane session lifecycle
  - Cons:
    - Adds schema, migration, and operational complexity around key management and token/session handling
    - Requires careful incremental rollout to avoid breaking current auth and test coverage
- Outcome: follow-on implementation planning now targets encrypted identity storage, blind-index login lookup, internal-user-id JWT subjects, refresh-token sessions, revocation/device tracking, and service trust for future media/private subservices.
- Follow-up actions:
  - Add encrypted identity persistence and blind-index lookup primitives
  - Migrate auth guard resolution from email subjects to internal user ids
  - Add refresh-session persistence, rotation, and revocation behavior
  - Define internal service credential shape for private subservices
- References: `docs/architecture.md`, `docs/roadmap.md`
