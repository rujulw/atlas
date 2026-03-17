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
- CSS

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

- Owner-scoped file listing and search
- Refresh-token sessions and device management
- Encrypted identity fields at rest
- Internal service trust for future subservices
- Observability tooling
- Tailnet-oriented production deployment hardening

These will be introduced incrementally.

## Development Workflow

1. Develop backend features in `server/app`.
2. Expose functionality through REST API endpoints.
3. Integrate frontend components with API routes.
4. Add database models and migrations as needed.
5. Containerize services for consistent deployments.

Atlas is intended to be fully runnable in local development before deployment to a home server environment.
