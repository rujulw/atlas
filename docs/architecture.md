# Architecture

## Overview

Atlas is a self-hosted personal cloud platform designed around a modular backend and private networking model.

The system runs on personal hardware and exposes services through a structured API. Clients connect through a secure private network instead of a publicly exposed endpoint.

Atlas is also intended to become the private identity core for future internal apps that run behind the same tailnet boundary.

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
- refresh flow through `/api/v1/auth/refresh`
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
- `GET /api/v1/files`: authenticated owner-scoped file listing with pagination, stable sorting, filename search, and metadata filters
- `GET /api/v1/files/{file_id}/download`: authenticated file download with owner-scoped metadata lookup

Current auth API surface:

- `POST /api/v1/auth/register`: create a user with hashed password persistence
- `POST /api/v1/auth/login`: verify credentials and issue an access-token plus refresh-token pair
- `POST /api/v1/auth/refresh`: validate a refresh session, rotate it, and mint a new access-token plus refresh-token pair
- `GET /api/v1/auth/me`: validate bearer token, resolve the internal user id, and return current user identity
- `GET /api/v1/auth/sessions`: list the current user's refresh sessions with device metadata and lifecycle state
- `DELETE /api/v1/auth/sessions/{session_identifier}`: revoke one refresh session
- `DELETE /api/v1/auth/sessions`: revoke all refresh sessions for the current user

FastAPI provides the primary HTTP API.

PostgreSQL stores structured metadata including:

- Users
- Files
- Permissions
- Indexing information

Current implemented metadata tables:

- `users`: authentication identity records
- `files`: owner-scoped file metadata (name, storage key, checksum, size, and lifecycle flags)
- `refresh_sessions`: persisted refresh-token session metadata for rotation, revocation, and device visibility

Current user identity baseline:

- `users.id`: internal integer identifier
- `users.email`: unique login identifier in plaintext today
- `users.email_blind_index`: deterministic email lookup value derived in application code
- `users.hashed_password`: one-way PBKDF2 password hash
- `users.full_name`: optional profile field in plaintext today

The next auth direction is to keep `hashed_password` as a one-way hash while moving sensitive identity fields such as email, username, and full name behind application-layer encryption and blind-index lookup support.

### Planned Identity Model

The next auth iteration should reshape identity storage around three kinds of user data:

- stable internal identifiers used for authorization and token subjects
- encrypted user-facing identity fields stored as ciphertext at rest
- blind indexes derived from normalized identity values for deterministic lookup

The intended user record shape is:

- `users.id`: internal primary key and future JWT subject source
- `users.hashed_password`: one-way password hash
- `users.email_ciphertext`: encrypted canonical email value
- `users.email_bidx`: blind index for canonical email equality lookup
- `users.username_ciphertext`: encrypted username value when usernames are enabled
- `users.username_bidx`: blind index for username equality lookup when usernames are enabled
- `users.full_name_ciphertext`: encrypted profile display name

The exact column names may change during implementation, but the separation of internal id, ciphertext fields, and blind indexes is the key design decision.

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

### Browsing and Search Direction

The current storage slice turns Atlas from an upload/download API into an owner-scoped file browser.

The core design choice is that browsing and search operate on file metadata records, not on raw filesystem paths and not on user-supplied owner identifiers.

The implemented browse/search contract is:

- every list or search query is implicitly scoped to the authenticated owner
- soft-deleted rows are excluded from normal browsing results
- results are paginated and must use deterministic ordering
- sortable fields are limited to explicit metadata columns owned by Atlas
- v1 search targets normalized filename-oriented metadata rather than full-text file content
- metadata filters should start from fields Atlas already persists reliably, such as MIME type, `size_bytes`, and creation/update timestamps

The current baseline query capabilities are:

- list most recent files for the current owner
- sort by backend-approved keys such as `created_at`, `updated_at`, `original_name`, or `size_bytes`
- search by filename text match with normalized case-handling
- filter by exact MIME type or MIME-type family if the implementation chooses a safe normalized form
- filter by file-size bounds and created-at windows for predictable metadata queries

This model exists for a few reasons:

- owner scope stays implicit because authorization already comes from Atlas auth, and accepting `owner_id` as a query input would create unnecessary cross-user risk
- stable sort keys are required before pagination is safe, otherwise pages drift as clients navigate
- metadata-first search matches what Atlas actually stores today and avoids promising content indexing that does not exist yet
- the first frontend storage shell needs stable browse/search primitives before UI work starts in earnest

The current response shape:

- reuse canonical file metadata fields already returned by upload/download flows where practical
- include page metadata or cursor state needed to continue iteration
- echo the active sort/filter/search constraints clearly enough for UI and debugging use

The intended non-goals of this first browse/search slice are:

- direct filesystem traversal semantics
- arbitrary user-defined query languages
- content indexing across file bodies
- directory trees or nested folder abstractions

Those can be layered later if Atlas grows a richer indexing model, but the initial owner-scoped browser remains intentionally narrow and predictable.

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
- login normalizes email input and resolves users through blind-index lookup with plaintext-email fallback for compatibility
- JWT access token validation is centralized through a shared dependency
- JWT subject now uses the internal user id instead of email
- refresh tokens are opaque `session_identifier.secret` values whose hashes are stored server-side
- refresh token use rotates the backing session and supports single-session or all-session revocation
- session listing exposes coarse device metadata (`device_name`, `user_agent`, `last_seen_ip`) plus lifecycle timestamps

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

The intended login lookup flow is:

1. Normalize the submitted identifier in application code.
2. Derive a blind index from the normalized value.
3. Query by blind index rather than raw email or username.
4. Decrypt the matching ciphertext field only after a candidate row is found.
5. Verify the canonical plaintext value before password verification succeeds.

This avoids using ciphertext directly for equality queries while still preventing the database from storing raw identity values.

The intended cryptographic boundaries are:

- passwords are always one-way hashed and are never encrypted
- blind indexes are used only for equality lookup, not value recovery
- ciphertext fields are decrypted only inside the application layer
- encryption and blind-index keys stay outside PostgreSQL
- normalization must happen before encryption and blind-index derivation so uniqueness behavior stays deterministic

### Session Direction

The intended session model is:

- short-lived access tokens for API requests
- longer-lived refresh tokens bound to persisted server-side sessions
- explicit revocation support
- device-aware session tracking with last-used metadata

This is the path from the current access-token-only baseline to a production-sane private-network auth model.

The planned refresh-session shape is:

- one persisted session per login/device context tied to the internal user id
- an opaque refresh token whose raw secret is held only by the client
- a stored hash of that refresh secret in the database rather than the raw token
- lifecycle metadata including creation, expiry, last use, and revocation timestamps
- coarse device metadata such as device label, user agent, and last seen IP

The current implementation follows this shape and stores refresh-session lifecycle state in the `refresh_sessions` table.

The planned refresh lifecycle is:

1. Login creates a persisted refresh session and returns both an access token and refresh token.
2. Normal API requests use only the short-lived access token.
3. Refresh requests validate the presented refresh secret against the stored session record.
4. Successful refresh rotates the refresh secret, updates session metadata, and invalidates the previous refresh token.
5. Revoked, expired, or replayed refresh tokens are denied and cannot mint fresh access tokens.

Revocation is intentionally server-driven:

- a single session can be revoked for logout-from-this-device behavior
- all sessions for a user can be revoked for compromise response or future password-reset flows
- access tokens are still treated as short-lived bearer credentials and are not individually tracked server-side

Device metadata is for operator and user visibility rather than strong identity proof. Atlas should store enough detail to power a "signed in devices" view without depending on invasive fingerprinting.

Implementation note:

- SQLite-backed tests may materialize timestamp columns as naive datetimes, so refresh/session comparisons normalize database values back to UTC inside the application layer before expiry checks.

### Internal Service Trust

Atlas should become the canonical identity layer for future private subservices on the same server.

In practical terms, Atlas is not just a storage API. It is intended to become the private account system and identity core for a broader self-hosted app ecosystem running behind the same tailnet boundary.

The expected trust shape is:

- Atlas issues stable user identity based on internal user ids rather than email
- private subservices validate Atlas-issued identity or dedicated internal service credentials
- services do not share user passwords or long-lived opaque user secrets
- service claims should explicitly model issuer, audience, expiry, and optional acting-user context

The deployment assumption is intentionally tailnet-first:

- Atlas is expected to run behind a private tailnet boundary rather than as a public internet identity provider
- future private subservices should sit behind the same private-network boundary or the same host-local network
- private-network reachability reduces exposure but does not itself grant trust
- end-user authentication terminates at Atlas rather than being repeated independently in each private subservice

The trust boundary is intentionally narrow:

- Atlas owns user passwords, refresh-token sessions, and primary user authentication
- downstream private services consume Atlas-issued identity or dedicated service credentials
- downstream services still own domain authorization for their own resources
- shared-host or shared-tailnet placement is not sufficient reason to skip explicit claim validation

This means Atlas should behave more like a private identity core than a catch-all monolith for every downstream policy decision.

The broader platform implication is:

- Atlas terminates end-user authentication
- Atlas issues user/session identity and internal service trust claims
- downstream services focus on their own product logic and resource authorization
- downstream services never need raw user passwords in order to participate in the platform

### Media Service Integration Shape

A future media service on the same private server should trust Atlas identity instead of implementing a separate user system.

The intended split is:

- Atlas owns authentication and session issuance
- the media service consumes Atlas-authenticated user or service identity
- media-specific authorization remains local to the media service
- both services remain reachable only through the private tailnet boundary

This is the model that would support future private apps such as:

- a media library service
- a music-streaming service
- a video-streaming service
- other domain-specific private apps that want shared identity without shared password storage

## Known Gaps

Current architecture does not yet include:

- Background worker system
- File versioning
- Advanced metadata indexing or content search
- Encrypted identity storage and blind indexes
- Observability stack
- Multi-node deployments

These features are planned in future development phases.
