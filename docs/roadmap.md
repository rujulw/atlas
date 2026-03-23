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
- Tailwind CSS v4 frontend migration
- Public client route structure for landing/docs/app entrypoints
- Branded landing page describing Atlas as a storage, auth, and trust platform
- Shared landing/app-shell components (`Navbar`, `LiquidGlass`, `Aurora`, `ProtectedAppShell`)
- Client interaction polish for smooth anchor scrolling, compact navbar behavior, and landing-page reveal animation
- Dockerized local development stack with diagnostics
- Owner-scoped upload/download storage pipeline with metadata persistence
- Owner-scoped file listing, pagination, search, and metadata-query support

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

Near-term implementation priorities after the completed storage browse/search backend slice:

- Build the authenticated storage shell inside the now-established `/app` route boundary
- Add auth-aware session bootstrap and browse-state handling in the client
- Expose upload, search, list, download, and empty/loading/error states in a usable file-browser UI
- Add frontend tests for auth-shell and storage-browser interactions
- Keep backend browse/search contracts stable while the client begins consuming them

Frontend-storage delivery constraints for this slice:

- the UI should treat Atlas auth as the only source of acting-user context
- storage browsing should consume the owner-scoped API contract as-is rather than reconstructing ownership or sort behavior client-side
- pagination, search, and filter state should map directly to backend query params
- the first storage UI should stay honest about current backend capabilities and not imply directory trees or content indexing that do not yet exist

Why this slice comes next:

- Atlas now has the backend primitives needed for day-to-day storage browsing
- the public client shell and landing surface now exist, but the authenticated storage experience still needs to be built inside `/app`
- media-library work should build on stable browse/search primitives and a real app shell rather than on ad hoc backend-only workflows

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
2. Land the public client shell and platform-direction landing experience.
3. Build the authenticated frontend storage shell against those stable browse/search APIs.
4. Add media-library metadata and service integration on top of Atlas identity and storage.
5. Return to deeper observability and other platform-hardening work as the product surface expands.

The public-client shell step is now in place, so the next frontend implementation pass should move into the protected application experience rather than revisiting the marketing shell again.

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
