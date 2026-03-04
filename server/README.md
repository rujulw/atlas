# Atlas Backend

This directory contains the FastAPI backend scaffold.

## Current scope

- App entrypoint (`app/main.py`)
- Module boundaries for API, core, models, schemas, services, and db
- Placeholder migration and test structure
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
