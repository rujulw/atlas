# Roadmap

## Goal

Atlas aims to become a modular self-hosted personal cloud platform that allows individuals to operate their own secure data infrastructure.

The project will evolve incrementally from a simple storage API to a full personal cloud ecosystem.

## Immediate Baseline

Initial development focuses on establishing a stable backend foundation.

Baseline features include:

- FastAPI backend
- PostgreSQL integration
- Basic file metadata models
- API structure
- Local storage system

Current baseline progress (completed):

- API versioned routing and health endpoint
- PostgreSQL + Alembic migration baseline
- User registration, password hashing, JWT login, and auth guard baseline
- React + Vite + TypeScript client bootstrap
- Client integration to backend health/auth endpoints
- Dockerized local development stack with diagnostics
- Owner-scoped upload/download storage pipeline with metadata persistence

## 1. Core Backend

Implement core infrastructure:

- Encrypted identity-aware authentication system
- File upload and download APIs
- Metadata database models
- API routing structure
- Database migrations

This phase establishes the functional backend.

## 2. Storage Services

Expand the storage layer:

- File indexing
- Search functionality
- Metadata extraction
- File browsing endpoints

Focus is placed on improving storage usability.

## 3. Media Services

Introduce media-focused features:

- Image preview generation
- Video streaming endpoints
- Media metadata extraction
- Photo management interface

## 4. Observability

Add operational tooling for monitoring:

- Structured logging
- Health check endpoints
- System metrics
- Performance monitoring

These features prepare Atlas for long-running production deployments.

## Next Priority Slice

Near-term implementation priorities after current baseline:

- Add encrypted identity fields and complete migration away from plaintext identity storage
- Migrate JWT subjects from email to internal user ids
- Introduce refresh-token sessions with revocation and device tracking
- Define service-to-service trust for future private subservices
- Add structured server logging for request tracing
- Add CI checks for backend tests and frontend type/build validation

Auth-specific delivery constraints for this slice:

- passwords stay hashed and are never switched to reversible encryption
- sensitive identity fields such as email, username, and full name move to application-layer encryption
- login lookup shifts to blind indexes instead of plaintext identity queries
- future internal subservices consume Atlas identity instead of introducing parallel auth systems

Design outputs required before implementation expands:

- document the planned user-record split between internal ids, ciphertext fields, and blind indexes
- define canonical normalization rules for email and username lookup inputs
- define where ciphertext verification happens relative to blind-index lookup and password verification
- document key-separation expectations for encryption versus blind-index derivation
- define the persisted refresh-session record, including hashed refresh secret storage and lifecycle timestamps
- define refresh rotation and replay-handling rules before refresh endpoints are introduced
- define the minimum device metadata Atlas tracks for session visibility and targeted revocation
- define tailnet-only deployment assumptions for Atlas and future private subservices
- define where end-user authentication terminates versus where internal service trust begins
- define issuer, audience, and service-principal expectations before cross-service auth claims are introduced

## Private Platform Direction

Atlas is now explicitly tracking a tailnet-only personal-cloud direction:

- private-network reachability over public exposure
- Atlas as the canonical identity layer for future internal services
- media-service integration built on Atlas-issued identity
- database compromise resilience through encrypted identity storage and blind indexes

Incremental sequence from here:

1. Add encrypted identity persistence and blind-index lookup without breaking the current auth flow.
2. Migrate access-token subjects and auth guards to internal user ids.
3. Introduce refresh-token-backed sessions with revocation and device tracking.
4. Add internal service trust primitives for private subservices on the same server.
5. Build the media-service integration on Atlas-issued identity rather than a separate auth layer.

The first of these steps is intentionally a design and schema-modeling pass before migration code lands.

## Open-Source Delivery Model

This repository is the public core for architecture, reusable services, and transparent development history.

Private repositories are expected to contain:

- Instance-specific website implementations
- Customer or personal deployment overlays
- Environment-specific secrets and internal integrations

Core features should be developed in this repository first, then consumed by private instance repos.
