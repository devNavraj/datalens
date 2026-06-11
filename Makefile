COMPOSE := docker compose --env-file .env -f docker/compose.dev.yml

.PHONY: dev down logs setup test lint fmt

.env:
	cp .env.example .env

dev: .env
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

setup:
	cd backend && uv venv && uv pip install -e ".[dev]"

test:
	cd backend && .venv/bin/pytest

lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy src

fmt:
	cd backend && .venv/bin/ruff format . && .venv/bin/ruff check --fix .
