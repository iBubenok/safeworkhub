PYTHON := .venv/bin/python
PIP := .venv/bin/pip
COMPOSE := docker-compose

DATABASE_URL_TEST ?= postgresql+asyncpg://safeworkhub:safeworkhub_dev@localhost:5432/safeworkhub_test
REDIS_URL_TEST ?= redis://localhost:6379/1
SECRET_KEY ?= test-secret-key-change-me-0123456789abcdef123456
VITE_API_URL ?= http://localhost:8000/api/v1

.PHONY: install-backend install-frontend lint-backend lint-frontend test-backend test-frontend build-backend build-frontend up down db-migrate format-backend lint test build

install-backend:
	$(PIP) install -r backend/requirements-dev.txt

install-frontend:
	cd frontend && npm ci

lint-backend:
	cd backend && ../.venv/bin/ruff check .

format-backend:
	cd backend && ../.venv/bin/ruff format

test-backend:
	cd backend && APP_ENV=testing SECRET_KEY=$(SECRET_KEY) DATABASE_URL=$(DATABASE_URL_TEST) REDIS_URL=$(REDIS_URL_TEST) ../.venv/bin/pytest tests

build-backend:
	cd backend && ../.venv/bin/python -m compileall app

lint-frontend:
	cd frontend && npm run lint && npm run type-check

test-frontend:
	cd frontend && npm run test

build-frontend:
	cd frontend && VITE_API_URL=$(VITE_API_URL) npm run build

lint: lint-backend lint-frontend

test: test-backend test-frontend

build: build-backend build-frontend

db-migrate:
	cd backend && APP_ENV=${APP_ENV:-development} ../.venv/bin/alembic upgrade head

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down -v
