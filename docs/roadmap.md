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

## 1. Core Backend

Implement core infrastructure:

- Authentication system
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

## Open-Source Delivery Model

This repository is the public core for architecture, reusable services, and transparent development history.

Private repositories are expected to contain:

- Instance-specific website implementations
- Customer or personal deployment overlays
- Environment-specific secrets and internal integrations

Core features should be developed in this repository first, then consumed by private instance repos.
