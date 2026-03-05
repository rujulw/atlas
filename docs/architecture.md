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

### File Metadata Schema (Planned v1)

The first storage metadata slice will introduce a `files` table with the following fields:

- `id`: integer primary key
- `owner_id`: foreign key to `users.id`, indexed, non-null
- `original_name`: client-provided filename, non-null
- `storage_key`: server-generated relative storage path key, unique, non-null
- `mime_type`: optional MIME type from upload metadata
- `size_bytes`: file size in bytes, non-null
- `checksum_sha256`: content checksum, non-null
- `is_deleted`: soft-delete flag, non-null default `false`
- `created_at`: timestamp with timezone, server default `now()`, non-null
- `updated_at`: timestamp with timezone, server default `now()`, non-null

### Storage Constraints (Planned v1)

Storage behavior for upload/download flows is constrained by the following rules:

- Path ownership: every file metadata row is scoped to `owner_id`; API reads must enforce owner match.
- Path safety: `storage_key` is server-generated and must never be accepted directly from user input.
- Disk scope: all file writes/reads must stay under a configured storage root directory.
- Integrity: `size_bytes` and `checksum_sha256` are stored at upload time and used for validation/diagnostics.
- Immutability baseline: file content is immutable in v1; updates are represented as new file records.
- Delete behavior: initial delete support is soft-delete (`is_deleted=true`) to preserve auditability.

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
