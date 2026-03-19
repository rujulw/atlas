# Bug Log

## 2026-03-18 - Avoided cross-user file enumeration in listing and search queries
- Status: fixed
- Severity: high
- Symptom: file browsing endpoints can leak another user's filenames, counts, or search hits if query logic is built as a generic metadata lookup instead of an auth-scoped repository query.
- Root cause: listing/search behavior was easy to add on top of the `files` table without forcing every query through the authenticated owner boundary.
- Fix: added owner-scoped repository query methods (`list_for_owner`, `count_for_owner`) and wired the listing endpoint so owner scope always comes from the authenticated subject instead of client input.
- Verification: repository and API tests cover owner-only listing/search behavior and prove another user's uploads do not affect returned items or totals.
- Files touched:
  - `server/app/repositories/file.py`
  - `server/app/api/routes/files.py`
  - `server/tests/unit/test_file_repository.py`
  - `server/tests/api/v1/test_files_integration.py`
- Linked commit/PR: pending
- Notes: this goes hand in hand with the earlier upload/download ownership model, so browsing did not become the place where storage isolation regressed.

## 2026-03-18 - Avoided unstable file pagination and sort drift in the first browse endpoint
- Status: fixed
- Severity: medium
- Symptom: paginated file listing can duplicate or skip rows across pages if sorting is left implicit or tied to unstable client-controlled fields.
- Root cause: the first listing endpoint needed a deterministic ordering contract before pagination became trustworthy.
- Fix: constrained list sorting to explicit metadata fields, added stable secondary `id` ordering in repository queries, and exposed typed pagination/sort parameters in the API response contract.
- Verification: repository and API tests cover paginated listing with stable ordering by `original_name`, including page-by-page result expectations.
- Files touched:
  - `server/app/repositories/file.py`
  - `server/app/schemas/file.py`
  - `server/app/api/routes/files.py`
  - `server/tests/unit/test_file_repository.py`
  - `server/tests/api/v1/test_files_integration.py`
- Linked commit/PR: pending
- Notes: this is why pagination/sorting landed before richer query exposure; the browse baseline needed deterministic behavior before it needed more knobs.

## 2026-03-18 - Avoided deleted-file visibility and ambiguous metadata-filter behavior in browse/search
- Status: fixed
- Severity: medium
- Symptom: file list/search routes can surface soft-deleted rows or behave unpredictably when range filters are inverted, which makes totals unreliable and user-visible query results confusing.
- Root cause: browse/search logic needed explicit handling for soft-delete exclusion and invalid size/time windows instead of relying on implicit empty results.
- Fix: repository queries exclude `is_deleted=true` rows by default, and the listing endpoint now validates size/time ranges before executing metadata-filtered searches.
- Verification: repository coverage excludes deleted rows from counts, and API tests verify soft-deleted files stay hidden plus invalid range filters return `400`.
- Files touched:
  - `server/app/repositories/file.py`
  - `server/app/api/routes/files.py`
  - `server/tests/unit/test_file_repository.py`
  - `server/tests/api/v1/test_files_integration.py`
- Linked commit/PR: pending
- Notes: this explains why the first metadata-query support is narrow and typed instead of silently accepting contradictory filter input.

## 2026-03-18 - Avoided refresh token replay leaving a rotated session chain active
- Status: fixed
- Severity: high
- Symptom: once refresh-token rotation exists, replaying an older refresh token can leave the newly rotated session usable unless reuse is treated as a compromise event.
- Root cause: simple refresh rotation revokes only the presented session unless the implementation explicitly invalidates the rest of the active session chain on token-hash mismatch or rotated-token reuse.
- Fix: refresh flow now revokes all active sessions for the user when a rotated token is replayed or when the stored refresh-token hash no longer matches the presented token.
- Verification: auth integration coverage proves that reusing an older refresh token returns `401` and invalidates the rotated replacement session as well.
- Files touched:
  - `server/app/api/routes/auth.py`
  - `server/tests/api/v1/test_auth_integration.py`
- Linked commit/PR: pending
- Notes: this is why refresh tokens were implemented as persisted server-side sessions with rotation metadata instead of as standalone long-lived bearer tokens.

## 2026-03-18 - Avoided internal route auth bypass via user access tokens or wrong audiences
- Status: fixed
- Severity: high
- Symptom: private service routes can accidentally accept normal user access tokens or tokens minted for the wrong audience if they reuse generic bearer validation without service-specific claim checks.
- Root cause: issuer and signature validation alone do not distinguish end-user API tokens from internal service credentials or enforce the intended target audience for machine-to-machine calls.
- Fix: added `require_service_auth(...)` with explicit service-token validation, expected internal audience enforcement, and `token_use=service` checks.
- Verification: dependency tests cover valid service access plus rejection of user access tokens, disallowed service names, and wrong internal audiences.
- Files touched:
  - `server/app/api/deps.py`
  - `server/tests/api/test_service_auth_dependency.py`
  - `server/app/services/auth.py`
- Linked commit/PR: pending
- Notes: this goes hand in hand with defining issuer/audience/service-principal claims before wiring internal trust into future services.

## 2026-03-18 - Avoided unauthorized acting-user impersonation in service-token scaffolding
- Status: fixed
- Severity: medium
- Symptom: an internal service token model can accidentally allow any trusted service to attach arbitrary acting-user context if impersonation is not gated separately from ordinary service identity.
- Root cause: service-principal scaffolding needs an explicit capability boundary for "can act as user" rather than treating all trusted services as interchangeable.
- Fix: service-token issuance now rejects acting-user context unless the principal is explicitly marked `can_act_as_user`, and service-auth dependencies can require acting-user context only where needed.
- Verification: unit and dependency tests cover rejection of unauthorized acting-user issuance and enforcement of acting-user requirements on internal routes.
- Files touched:
  - `server/app/services/auth.py`
  - `server/app/api/deps.py`
  - `server/tests/unit/test_auth_token_service.py`
  - `server/tests/api/test_service_auth_dependency.py`
- Linked commit/PR: pending
- Notes: this is why internal service trust was modeled with explicit principal capabilities instead of one shared "trusted service" credential shape.

## 2026-03-05 - Debugged storage access control and missing-content edge paths via API integration suite
- Status: fixed
- Severity: high
- Symptom: without end-to-end coverage, download ownership enforcement and missing-blob behavior can silently regress across route/repository/storage refactors.
- Root cause: storage API behavior spanned multiple layers without explicit integration assertions for failure contracts.
- Fix: added integration tests validating owner-only download success, invalid-owner `404`, and missing-content `404` behavior.
- Verification: storage integration test module now exercises upload->download roundtrip plus ownership/content failure paths.
- Files touched:
  - `server/tests/api/v1/test_files_integration.py`
- Linked commit/PR: pending
- Notes: this is the quality gate for the storage metadata flow branch before listing/observability work.

## 2026-03-05 - Avoided cross-user file read via metadata lookup scope
- Status: fixed
- Severity: high
- Symptom: download endpoints can leak files if metadata lookup is done by file id only without owner scoping.
- Root cause: missing owner-bound read method in file repository.
- Fix: added `get_by_id_for_owner(file_id, owner_id)` and used it in download endpoint before blob reads.
- Verification: download route now returns `404` when file id is not present for authenticated owner.
- Files touched:
  - `server/app/repositories/file.py`
  - `server/app/api/routes/files.py`
- Linked commit/PR: pending
- Notes: forms the authorization baseline for upcoming storage listing/downloading behavior.

## 2026-03-05 - Avoided unsafe path resolution in download response path
- Status: fixed
- Severity: high
- Symptom: tampered or malformed storage keys can produce unsafe filesystem reads if route handlers bypass path validation.
- Root cause: route-level direct file reads risk skipping storage root checks.
- Fix: download path uses `BlobStorageService.read_bytes`, which validates resolved key paths under configured root and maps invalid paths to not-found responses.
- Verification: download endpoint catches invalid-path and missing-file errors and returns controlled `404` responses.
- Files touched:
  - `server/app/api/routes/files.py`
  - `server/app/services/storage.py`
- Linked commit/PR: pending
- Notes: prevents path traversal disclosure via storage metadata corruption or bad keys.

## 2026-03-05 - Avoided upload path injection via client filename
- Status: fixed
- Severity: high
- Symptom: multipart uploads can accidentally use user-controlled filenames as storage paths, enabling traversal or unsafe writes.
- Root cause: missing server-side storage-key generation boundary in upload implementation.
- Fix: upload route now relies on `StorageKeyService` (`UUIDStorageKeyService`) and local storage root validation before writes.
- Verification: upload writes are keyed by generated owner-scoped storage keys; local blob storage rejects invalid resolved paths.
- Files touched:
  - `server/app/api/routes/files.py`
  - `server/app/services/storage.py`
- Linked commit/PR: pending
- Notes: preventative control for forthcoming download path handling.

## 2026-03-05 - Avoided metadata/blob divergence in upload flow
- Status: fixed
- Severity: medium
- Symptom: upload handlers can return success without persisting integrity metadata, creating untraceable blobs.
- Root cause: no structured upload response contract tied to persisted metadata.
- Fix: added upload response schema and repository-backed metadata create path carrying `size_bytes`, `checksum_sha256`, and ownership.
- Verification: upload endpoint returns persisted metadata fields after successful file write + DB insert flow.
- Files touched:
  - `server/app/api/routes/files.py`
  - `server/app/repositories/file.py`
  - `server/app/schemas/file.py`
- Linked commit/PR: pending
- Notes: download/list endpoints can now rely on metadata as canonical source.

## 2026-03-05 - Avoided orphaned or inconsistent file metadata records
- Status: fixed
- Severity: high
- Symptom: storage metadata can drift from user ownership if file rows are created without foreign-key constraints and explicit schema guarantees.
- Root cause: no concrete `files` table implementation existed yet to enforce relational integrity.
- Fix: added `files` model and migration with `owner_id -> users.id` FK, unique `storage_key`, and non-negative size constraint.
- Verification: migration `20260305_0003_create_files` defines table constraints and indexes aligned with storage design contract.
- Files touched:
  - `server/app/models/file.py`
  - `server/app/models/__init__.py`
  - `server/app/db/base.py`
  - `server/migrations/versions/20260305_0003_create_files.py`
- Linked commit/PR: pending
- Notes: prevents downstream upload/download logic from persisting metadata that cannot be safely authorized.

## 2026-03-05 - Avoided route-storage coupling before upload endpoint implementation
- Status: fixed
- Severity: medium
- Symptom: upcoming upload/download route handlers risk direct filesystem coupling, making ownership/path safety rules hard to enforce consistently.
- Root cause: missing explicit storage service contracts before endpoint implementation.
- Fix: introduced storage protocol interfaces (`StorageKeyService`, `BlobStorageService`) and immutable write-result contract (`StoredFileObject`).
- Verification: service contracts exist in `app/services/storage.py` and are exported for use by upcoming storage endpoints.
- Files touched:
  - `server/app/services/storage.py`
  - `server/app/services/__init__.py`
- Linked commit/PR: pending
- Notes: this is a preventative architecture fix to keep storage behavior centralized and testable.

## 2026-03-05 - Avoided storage path traversal and cross-user access drift in design phase
- Status: fixed
- Severity: high
- Symptom: file upload/download implementations can accidentally trust client-provided paths or skip owner checks, enabling traversal or cross-user reads.
- Root cause: missing explicit storage constraints before endpoint implementation.
- Fix: documented storage constraints requiring server-generated `storage_key`, root-scoped disk access, and owner-scoped metadata queries.
- Verification: architecture + design docs now define the `files` schema and constraint contract used by upcoming storage implementation commits.
- Files touched:
  - `docs/architecture.md`
  - `docs/design.md`
- Linked commit/PR: pending
- Notes: this is a preventative design control to harden storage APIs before code lands.

## 2026-03-05 - Avoided metadata integrity ambiguity for file lifecycle
- Status: fixed
- Severity: medium
- Symptom: without explicit checksum/size metadata and delete semantics, storage APIs risk inconsistent validation and destructive delete behavior.
- Root cause: file lifecycle invariants were not yet codified in project docs.
- Fix: defined `size_bytes`, `checksum_sha256`, and `is_deleted` in the planned schema, with immutable-content baseline and soft-delete behavior.
- Verification: storage schema section now exists in architecture and linked design decision entry.
- Files touched:
  - `docs/architecture.md`
  - `docs/design.md`
- Linked commit/PR: pending
- Notes: reduces migration churn and supports future auditing/indexing flows.

## 2026-03-05 - Avoided auth bypass on protected routes
- Status: fixed
- Severity: high
- Symptom: protected endpoints could be implemented without consistent token checks, allowing accidental anonymous access.
- Root cause: no shared auth guard dependency to enforce bearer validation at route boundaries.
- Fix: added `get_current_subject` dependency with explicit bearer token requirement and JWT validation (`signature`, `exp`, `sub`).
- Verification: `/api/v1/auth/me` returns `401` on missing/invalid token and `200` with authenticated subject for valid JWT.
- Files touched:
  - `server/app/api/routes/auth.py`
  - `server/app/services/auth.py`
  - `server/tests/api/v1/test_auth.py`
  - `server/tests/unit/test_auth_token_service.py`
- Linked commit/PR: pending
- Notes: this is a preventative control that centralizes auth checks for future protected endpoints.

## 2026-03-05 - Avoided JWT validation edge-case failures
- Status: fixed
- Severity: medium
- Symptom: token parsing and validation can fail unpredictably if base64url padding, malformed payloads, or signature comparisons are handled loosely.
- Root cause: JWT consumers commonly skip strict structure checks and constant-time signature verification.
- Fix: added strict 3-part token parsing, base64url decode handling, header/claim validation, and `hmac.compare_digest` signature checks.
- Verification: token service unit tests cover valid token verification and expired token rejection.
- Files touched:
  - `server/app/services/auth.py`
  - `server/tests/unit/test_auth_token_service.py`
- Linked commit/PR: pending
- Notes: reduces production risk from malformed-token behavior and timing-attack-prone signature comparisons.

## 2026-03-05 - TypeScript initialization errors in client scaffold
- Status: fixed
- Severity: medium
- Symptom: editor/TypeScript server reported JSX/type initialization errors in the client.
- Root cause: app tsconfig constrained `types` too tightly, and Node type definitions were missing for Vite config context.
- Fix: removed restrictive `types` override in app tsconfig and added `@types/node` to client dev dependencies.
- Verification: TypeScript diagnostics clear for client app and Vite config files.
- Files touched:
  - `client/tsconfig.app.json`
  - `client/package.json`
  - `client/src/App.tsx`
  - `client/src/components/StatusCard.tsx`
- Linked commit/PR: pending
- Notes: avoids cross-editor inconsistency in TS language service behavior.

## 2026-03-05 - Avoided runtime drift with containerized local stack
- Status: fixed
- Severity: medium
- Symptom: local environment setup risked diverging across machines (Python/Node/db versions and startup order).
- Root cause: host-only startup paths without a single shared orchestration contract.
- Fix: introduced `docker/docker-compose.yml`, service Dockerfiles, and Makefile `docker-*` diagnostics targets.
- Verification: compose stack exposes deterministic db/server/client services and health diagnostics.
- Files touched:
  - `docker/docker-compose.yml`
  - `docker/server.Dockerfile`
  - `docker/client.Dockerfile`
  - `Makefile`
- Linked commit/PR: pending
- Notes: this is both a fix and a preventative control for onboarding and CI parity.

## 2026-03-04 - Avoided API contract breakage via versioned routing
- Status: fixed
- Severity: low
- Symptom: early endpoints could have shipped as unversioned paths and become hard to evolve safely.
- Root cause: no versioning boundary at initial API exposure.
- Fix: all initial routes mounted under `/api/v1/*`.
- Verification: health and auth routes resolve through versioned prefix.
- Files touched:
  - `server/app/api/router.py`
  - `server/app/api/v1/router.py`
- Linked commit/PR: pending
- Notes: prevents future v2 migration pain for both public and private consuming repos.

## 2026-03-04 - Health endpoint baseline added
- Status: fixed
- Severity: low
- Symptom: No canonical liveness endpoint for backend monitoring.
- Root cause: API scaffold existed without operational route contracts.
- Fix: Added `/api/v1/health` endpoint with top-level router registration.
- Verification: `make test-server` includes `server/tests/api/v1/test_health.py`.
- Files touched:
  - `server/app/api/router.py`
  - `server/app/api/v1/router.py`
  - `server/app/api/routes/health.py`
  - `server/app/main.py`
  - `server/tests/api/v1/test_health.py`
- Linked commit/PR: pending
- Notes: this serves as the template for future endpoint-level operational checks.
