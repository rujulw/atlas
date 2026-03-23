# Atlas

A self-hosted personal cloud platform for secure storage, private networking, and remote access to personal data services.

The system is designed to run on personal hardware (for example, a Mac mini home server) while remaining reachable from authorized devices through a private mesh network.

## Vision

Atlas emphasizes:

- Data ownership
- Privacy-first infrastructure
- Modular services
- Reproducible deployments
- Developer-friendly APIs

This repository is the public core. Instance-specific websites and deployment customizations are expected to live in private repositories.

Atlas is also explicitly moving toward a tailnet-only platform shape where Atlas becomes the private identity core for future self-hosted apps, not just a standalone storage API.

## Documentation

- [Architecture](docs/architecture.md): System structure, runtime model, and security boundaries
- [Roadmap](docs/roadmap.md): Planned implementation phases and milestones

## Tech Stack

### Backend

- Python
- FastAPI
- PostgreSQL
- Alembic
- Redis (optional)
- Docker

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS v4
- React Router
- Framer Motion

## Project Structure

```text
atlas/
├── server/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── core/
│   │   └── main.py
│   └── migrations/
├── client/
│   ├── src/
│   └── index.html
├── docs/
│   ├── architecture.md
│   └── roadmap.md
├── docker/
│   └── docker-compose.yml
└── README.md
```

## Quick Start

### 1. Start backend

```bash
make install-server-dev
make run-server
```

### 2. Start frontend

```bash
cd client
npm install
npm run dev
```

## Docker Development Stack

Run the full local stack (PostgreSQL, backend, frontend):

```bash
make docker-up
```

Useful diagnostics:

```bash
make docker-ps
make docker-health
make docker-logs
```

## Environment Variables

### Server (`server/.env`)

```env
DATABASE_URL=
REDIS_URL=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=
REFRESH_TOKEN_EXPIRE_DAYS=
IDENTITY_ENCRYPTION_KEY=
IDENTITY_BLIND_INDEX_KEY=
IDENTITY_KEY_VERSION=
STORAGE_ROOT_PATH=
```

### Client (`client/.env`)

```env
VITE_API_URL=http://localhost:8000
```

## Current Gaps

Current version focuses on establishing the private-cloud backend baseline.

Missing features include:

- Frontend storage shell for authenticated list/search/upload/download flows
- Encrypted identity fields at rest
- Internal service trust for future subservices
- Observability tooling
- Tailnet-oriented production deployment hardening

These will be introduced incrementally.

## Auth API Baseline

Current auth/session endpoints:

- `POST /api/v1/auth/register`: create a user with hashed password persistence
- `POST /api/v1/auth/login`: verify credentials and issue an access-token plus refresh-token pair
- `POST /api/v1/auth/refresh`: rotate a valid refresh token and mint a new access-token plus refresh-token pair
- `GET /api/v1/auth/me`: validate bearer token and return the current user identity
- `GET /api/v1/auth/sessions`: list the current user's known refresh sessions and device metadata
- `DELETE /api/v1/auth/sessions/{session_identifier}`: revoke a single refresh session
- `DELETE /api/v1/auth/sessions`: revoke all refresh sessions for the current user

Current token/session behavior:

- access tokens are short-lived signed JWTs with the internal user id as `sub`
- login and refresh responses return both `access_token` and `refresh_token`
- refresh tokens are opaque rotating bearer secrets backed by persisted server-side sessions
- Atlas stores only a hash of the refresh token secret, not the raw refresh token

## Storage API Baseline

Current storage endpoints:

- `POST /api/v1/files/upload`: store a file and persist owner-scoped metadata
- `GET /api/v1/files`: list the current owner's files with pagination, sorting, filename search, and metadata filters
- `GET /api/v1/files/{file_id}/download`: download a file only when it belongs to the authenticated owner

Current storage-query behavior:

- file browsing is always scoped to the authenticated owner
- listing supports `limit`, `offset`, `sort_field`, and `sort_direction`
- filename search is metadata-first and does not search file contents
- metadata filters support exact MIME type plus size/time-window bounds
- soft-deleted files are excluded from normal browse/search results

## Platform Direction

Atlas is being built as:

- a private account and session system
- a storage and metadata core
- a trust anchor for future private subservices on the same host or tailnet

That means future apps such as a media service should be able to trust Atlas-issued identity instead of building a second password/session system from scratch.

The intended split is:

- Atlas owns end-user authentication
- Atlas owns session issuance and refresh lifecycle
- Atlas provides stable internal identity and internal service trust primitives
- future private apps consume Atlas-issued identity instead of storing user passwords themselves

This is the path from "self-hosted file API" toward "private platform core" for future apps like media, photo, or document services.

## Current Client Surface

The client now includes:

- a branded landing page at `/`
- a placeholder docs route at `/docs`
- a protected app route scaffold at `/app`
- shared landing components for navbar, background motion, and glass/surface treatments
- smooth in-page anchor navigation and viewport-triggered landing-page reveal animations

This is still a product-direction shell rather than a complete storage browser, but it now reflects Atlas as a private storage, session, and trust platform instead of only exposing auth test controls.

## Development Workflow

1. Develop backend features in `server/app`.
2. Expose functionality through REST API endpoints.
3. Integrate frontend components with API routes.
4. Add database models and migrations as needed.
5. Containerize services for consistent deployments.

Atlas is intended to be fully runnable in local development before deployment to a home server environment.
