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

Near-term implementation priorities after the current auth/session and service-trust baseline:

- Define the owner-scoped file browsing, search, and metadata-query model
- Add repository query methods and schemas for predictable list/search behavior
- Ship an authenticated list endpoint with pagination and stable sorting
- Add filename search plus metadata filters for MIME type, size, and created-at windows
- Cover ownership isolation and filter semantics with API tests before frontend storage-shell work begins

Storage-browse delivery constraints for this slice:

- browse and search stay implicitly bound to the authenticated owner
- listing/search results operate on metadata rows, not raw filesystem paths
- soft-deleted files stay out of default browse/search responses
- sorting is limited to explicit backend-owned metadata fields
- v1 search remains metadata-oriented and does not imply body-content indexing
- query inputs should stay narrow and typed rather than growing into a free-form filter language

Design outputs required before implementation expands:

- document the owner-scoped browse/search contract and why `owner_id` stays out of client query inputs
- define the initial pagination and stable-sort rules
- define the baseline searchable/filterable metadata fields
- document filename normalization expectations for search behavior
- define list response metadata needed for page continuation and UI state
- document which search/indexing capabilities are intentionally out of scope for the first storage-browser slice

Why this slice comes next:

- Atlas already has secure upload/download behavior, but it is still missing the core usability layer needed for day-to-day browsing
- file listing/search needs to stabilize before the storage UI can be built without churn
- metadata-query contracts laid down here also become the base for later media-library and indexing work

## Private Platform Direction

Atlas is now explicitly tracking a tailnet-only personal-cloud direction:

- private-network reachability over public exposure
- Atlas as the canonical identity layer for future internal services
- media-service integration built on Atlas-issued identity
- database compromise resilience through encrypted identity storage and blind indexes

What this means at the product level:

- Atlas should grow into the shared account and session system for a broader private app ecosystem
- future private apps should trust Atlas for identity instead of building duplicate password/session systems
- Atlas should remain focused on identity, session, storage, and trust primitives rather than absorbing every downstream product concern

Incremental sequence from here:

1. Add owner-scoped file browsing, pagination, and search primitives on top of the existing storage metadata model.
2. Build the frontend storage shell against those stable browse/search APIs.
3. Add media-library metadata and service integration on top of Atlas identity and storage.
4. Return to deeper observability and other platform-hardening work as the product surface expands.

The first of these steps is intentionally a design pass before repository and endpoint code lands.

The intended payoff of this sequence is that Atlas becomes:

- the private login/account core
- the persistent storage core
- a usable owner-scoped file browser
- the trust anchor for future apps such as media, photo, or document services

## Open-Source Delivery Model

This repository is the public core for architecture, reusable services, and transparent development history.

Private repositories are expected to contain:

- Instance-specific website implementations
- Customer or personal deployment overlays
- Environment-specific secrets and internal integrations

Core features should be developed in this repository first, then consumed by private instance repos.
