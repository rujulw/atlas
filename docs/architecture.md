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

For local development, ports are published to the host. For the intended home-server deployment model, Atlas is expected to sit behind a tailnet-accessible private network boundary rather than a public ingress.

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

Current client baseline:

- health check call to `/api/v1/health`
- registration flow through `/api/v1/auth/register`
- login flow through `/api/v1/auth/login`
- bearer token storage in local component state for development verification

## Backend (`server`)

The backend is responsible for:

- Authentication
- File metadata management
- Storage orchestration
- Indexing services
- System monitoring

Current storage API surface:

- `POST /api/v1/files/upload`: authenticated multipart upload with metadata persistence
- `GET /api/v1/files/{file_id}/download`: authenticated file download with owner-scoped metadata lookup

Current auth API surface:

- `POST /api/v1/auth/register`: create a user with hashed password persistence
- `POST /api/v1/auth/login`: verify credentials and issue a signed JWT access token
- `GET /api/v1/auth/me`: validate bearer token and return current token subject

FastAPI provides the primary HTTP API.

PostgreSQL stores structured metadata including:

- Users
- Files
- Permissions
- Indexing information

Current implemented metadata tables:

- `users`: authentication identity records
- `files`: owner-scoped file metadata (name, storage key, checksum, size, and lifecycle flags)

Current user identity baseline:

- `users.id`: internal integer identifier
- `users.email`: unique login identifier in plaintext today
- `users.hashed_password`: one-way PBKDF2 password hash
- `users.full_name`: optional profile field in plaintext today

The next auth direction is to keep `hashed_password` as a one-way hash while moving sensitive identity fields such as email, username, and full name behind application-layer encryption and blind-index lookup support.

## Storage Layer

Atlas separates **file data** from **metadata**.

File contents are stored directly on disk while the database tracks:

- file paths
- ownership
- permissions
- indexing data

This allows large files to be stored efficiently without database overhead.

### File Metadata Schema (Implemented Baseline)

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

### Storage Constraints (Implemented Baseline + Service Contracts)

Storage behavior for upload/download flows is constrained by the following rules:

- Path ownership: every file metadata row is scoped to `owner_id`; API reads must enforce owner match.
- Path safety: `storage_key` is server-generated and must never be accepted directly from user input.
- Disk scope: all file writes/reads must stay under a configured storage root directory.
- Integrity: `size_bytes` and `checksum_sha256` are stored at upload time and used for validation/diagnostics.
- Immutability baseline: file content is immutable in v1; updates are represented as new file records.
- Delete behavior: initial delete support is soft-delete (`is_deleted=true`) to preserve auditability.
- Service boundaries: storage interfaces separate key generation from binary I/O (`StorageKeyService`, `BlobStorageService`) before concrete implementations are added.

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

Current implementation details:

- passwords are hashed with PBKDF2 and never encrypted for reversible recovery
- login currently looks users up by plaintext email
- JWT access token validation is centralized through a shared dependency
- JWT subject currently uses email and should migrate to an internal user id

Next-direction constraints:

- Atlas remains tailnet-only and should not assume public-internet exposure
- auth subjects should become stable internal user ids so future subservices can trust Atlas-issued identities
- refresh-token sessions, revocation, and device tracking should sit beside short-lived access tokens
- service-to-service trust for future private subservices should be modeled explicitly rather than sharing user credentials

### Identity Protection Direction

The intended privacy model for user identity is:

- normalize login identifiers in application code
- store sensitive identity fields as application-encrypted ciphertext
- derive blind indexes for deterministic equality lookup during login and uniqueness checks
- keep encryption keys outside the database in server configuration suitable for self-hosted deployment

This is meant to reduce the exposure of user identity data if the database is compromised while preserving practical login behavior.

### Session Direction

The intended session model is:

- short-lived access tokens for API requests
- longer-lived refresh tokens bound to persisted server-side sessions
- explicit revocation support
- device-aware session tracking with last-used metadata

This is the path from the current access-token-only baseline to a production-sane private-network auth model.

### Internal Service Trust

Atlas should become the canonical identity layer for future private subservices on the same server.

The expected trust shape is:

- Atlas issues stable user identity based on internal user ids rather than email
- private subservices validate Atlas-issued identity or dedicated internal service credentials
- services do not share user passwords or long-lived opaque user secrets
- service claims should explicitly model issuer, audience, expiry, and optional acting-user context

### Media Service Integration Shape

A future media service on the same private server should trust Atlas identity instead of implementing a separate user system.

The intended split is:

- Atlas owns authentication and session issuance
- the media service consumes Atlas-authenticated user or service identity
- media-specific authorization remains local to the media service
- both services remain reachable only through the private tailnet boundary

## Known Gaps

Current architecture does not yet include:

- Background worker system
- File versioning
- Refresh token session management
- Encrypted identity storage and blind indexes
- Internal service trust contracts for future subservices
- Observability stack
- Multi-node deployments

These features are planned in future development phases.
