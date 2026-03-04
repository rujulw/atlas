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
