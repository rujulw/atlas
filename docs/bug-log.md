# Bug Log

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
