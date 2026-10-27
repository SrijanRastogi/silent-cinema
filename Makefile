SHELL := /bin/bash
export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv
NPM ?= npm
COMPOSE ?= docker compose

.PHONY: help bootstrap doctor check lint format-check typecheck test test-integration test-media build migrate migrate-down dev dev-api dev-web docs-check fixture

help:
	@echo "bootstrap         install backend and frontend dependencies"
	@echo "doctor            check local prerequisites"
	@echo "check             run the full local quality gate"
	@echo "lint              Ruff, MyPy, ESLint"
	@echo "format-check      Ruff format check, Prettier check"
	@echo "typecheck         TypeScript project check"
	@echo "test              unit tests (backend + frontend)"
	@echo "test-integration  backend integration tests (needs PostgreSQL)"
	@echo "test-media        detection/OCR tests (needs FFmpeg + Tesseract)"
	@echo "build             production frontend build"
	@echo "migrate           apply all Alembic migrations"
	@echo "migrate-down      roll back the latest migration"
	@echo "dev               run API and web dev servers together"
	@echo "docs-check        validate documentation links and formatting"
	@echo "fixture           regenerate the synthetic intertitle fixture"

bootstrap:
	$(UV) sync
	cd apps/web && $(NPM) ci

doctor:
	$(UV) run python scripts/doctor.py

lint:
	$(UV) run ruff check .
	$(UV) run mypy
	cd apps/web && $(NPM) run lint

format-check:
	$(UV) run ruff format --check .
	cd apps/web && $(NPM) run format:check

typecheck:
	cd apps/web && $(NPM) run typecheck

test:
	$(UV) run pytest -m "not integration and not media"
	cd apps/web && $(NPM) test

test-integration:
	$(UV) run pytest -m integration

test-media:
	$(UV) run pytest -m media

check: lint format-check typecheck test build docs-check

build:
	cd apps/web && $(NPM) run build

migrate:
	$(UV) run alembic upgrade head

migrate-down:
	$(UV) run alembic downgrade -1

dev:
	$(MAKE) -j2 dev-api dev-web

dev-api:
	$(UV) run uvicorn silent_cinema.app:app --app-dir apps/api --reload --host 127.0.0.1 --port 8000

dev-web:
	cd apps/web && $(NPM) run dev

docs-check:
	$(UV) run python scripts/check_docs.py

fixture:
	$(UV) run python scripts/generate_fixture.py
