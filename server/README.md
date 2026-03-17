# Atlas Backend

This directory contains the FastAPI backend for Atlas.

## Current scope

- App entrypoint (`app/main.py`)
- Module boundaries for API, core, models, schemas, services, repositories, and db
- Alembic migrations for users and files
- PBKDF2 password hashing + JWT access token auth baseline
- Identity crypto settings, blind-index lookup, and encrypted user-field scaffolding
- File upload/download routes with metadata persistence
- Dependency management and development tooling

## Local development

From the repository root:

```bash
make install-server-dev
make run-server
```

Useful commands:

- `make test-server`
- `make lint-server`
- `make format-server`
- `make typecheck-server`
- `make db-upgrade`
- `make db-downgrade`
