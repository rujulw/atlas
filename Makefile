SHELL := /bin/bash

.DEFAULT_GOAL := help

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
SERVER_DIR ?= server
CLIENT_DIR ?= client
NPM ?= npm
UVICORN_APP ?= app.main:app
HOST ?= 127.0.0.1
PORT ?= 8000

.PHONY: help install-server install-server-dev run-server test-server lint-server format-server typecheck-server db-upgrade db-downgrade install-client run-client build-client typecheck-client clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"; printf "\nAtlas development commands\n\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-24s %s\n", $$1, $$2} END {printf "\n"}' $(MAKEFILE_LIST)

install-server: ## Install backend runtime dependencies
	cd $(SERVER_DIR) && $(PIP) install -r requirements.txt

install-server-dev: ## Install backend dev dependencies
	cd $(SERVER_DIR) && $(PIP) install -r requirements-dev.txt

run-server: ## Run FastAPI backend with autoreload
	cd $(SERVER_DIR) && $(PYTHON) -m uvicorn $(UVICORN_APP) --host $(HOST) --port $(PORT) --reload

test-server: ## Run backend tests
	cd $(SERVER_DIR) && $(PYTHON) -m pytest

lint-server: ## Run backend lint checks
	cd $(SERVER_DIR) && $(PYTHON) -m ruff check app tests

format-server: ## Format backend code
	cd $(SERVER_DIR) && $(PYTHON) -m black app tests
	cd $(SERVER_DIR) && $(PYTHON) -m ruff format app tests

typecheck-server: ## Run backend type checks
	cd $(SERVER_DIR) && $(PYTHON) -m mypy app

db-upgrade: ## Run latest database migrations
	cd $(SERVER_DIR) && $(PYTHON) -m alembic -c migrations/alembic.ini upgrade head

db-downgrade: ## Roll back one database migration
	cd $(SERVER_DIR) && $(PYTHON) -m alembic -c migrations/alembic.ini downgrade -1

install-client: ## Install frontend dependencies
	cd $(CLIENT_DIR) && $(NPM) install

run-client: ## Run frontend dev server
	cd $(CLIENT_DIR) && $(NPM) run dev

build-client: ## Build frontend bundle
	cd $(CLIENT_DIR) && $(NPM) run build

typecheck-client: ## Run frontend type checks
	cd $(CLIENT_DIR) && $(NPM) exec tsc -b

clean: ## Remove common local caches
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
