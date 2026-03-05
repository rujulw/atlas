# Bug Log

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
- Verification: health and auth stubs resolve through versioned prefix.
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
