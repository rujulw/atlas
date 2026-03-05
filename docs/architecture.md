# Architecture

## Overview

Atlas is a self-hosted personal cloud platform designed around a modular backend and private networking model.

The system runs on personal hardware and exposes services through a structured API. Clients connect through a secure private network instead of a publicly exposed endpoint.

Primary architectural goals:

- Privacy-first infrastructure
- Local-first deployment
- Modular service boundaries
- API-driven integration
- Reproducible environments

## Repository Structure

```text
atlas/
├── server/
├── client/
├── docs/
├── docker/
└── README.md
```

### server

Backend application providing APIs for storage, authentication, and system services.

### client

Web interface for interacting with the Atlas server.

### docs

Project documentation including architecture and roadmap.

### docker

Container definitions and deployment configurations.

## Runtime Architecture

All components run inside containers and communicate through internal Docker networking.

## Local Container Topology

Development stack uses `docker/docker-compose.yml` with three services:

- `db`: PostgreSQL metadata store (`5432`)
- `server`: FastAPI backend (`8000`)
- `client`: Vite/React frontend (`5173`)

The backend waits for database health before startup and applies migrations on boot.
Frontend depends on backend availability and targets `VITE_API_URL=http://localhost:8000`.

### Runtime Diagnostics

Operational diagnostics are exposed through:

- `make docker-ps` for service state
- `make docker-logs` for aggregated service logs
- `make docker-health` for quick API liveness verification

## Frontend (`client`)

The frontend is a lightweight web application responsible for:

- User authentication
- Browsing stored files
- Uploading and downloading content
- Interacting with the Atlas API

The client communicates exclusively with the backend API.

## Backend (`server`)

The backend is responsible for:

- Authentication
- File metadata management
- Storage orchestration
- Indexing services
- System monitoring

FastAPI provides the primary HTTP API.

PostgreSQL stores structured metadata including:

- Users
- Files
- Permissions
- Indexing information

## Storage Layer

Atlas separates **file data** from **metadata**.

File contents are stored directly on disk while the database tracks:

- file paths
- ownership
- permissions
- indexing data

This allows large files to be stored efficiently without database overhead.

## Synchronization Model

Atlas uses an API-driven synchronization model.

Clients interact with the server through structured API endpoints:

Future versions may introduce background workers for:

- File indexing
- Metadata extraction
- Media processing

## Security Model

Security is implemented across multiple layers.

### Network Isolation

The server is not exposed publicly.

Access is restricted through a private mesh network.

### Encryption

Network communication uses encrypted tunnels.

### Authentication

Application-level authentication protects API endpoints.

## Known Gaps

Current architecture does not yet include:

- Full authentication implementation
- Background worker system
- File versioning
- Observability stack
- Multi-node deployments

These features are planned in future development phases.
