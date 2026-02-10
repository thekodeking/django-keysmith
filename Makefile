PYTHON := uv run python
PIP    := uv pip

PACKAGE := keysmith
DJANGO_MANAGE := uv run --active python dev/manage.py

.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "Keysmith – Development Commands"
	@echo "--------------------------------"
	@echo "make setup          Setup venv and perform deps installation"
	@echo "make sync           Sync deps from lockfile"
	@echo "make test           Run test suite"
	@echo "make lint           Run linters"
	@echo "make format         Auto-format code"
	@echo "make check          Lint + tests"
	@echo "make clean          Remove caches/build artifacts"
	@echo "make build          Build package"
	@echo "make makemigrations Generate migrations for keysmith app"
	@echo "make migration-check Ensure model changes are captured in migrations"
	@echo "make migrate-dev    Apply migrations in local dev DB"
	@echo ""

setup:
	uv venv
	uv sync --dev

sync:
	uv sync --dev

test:
	uv run pytest

lint:
	uv run ruff check $(PACKAGE)

format:
	uv run ruff format $(PACKAGE)

check: lint test

build:
	uv build

makemigrations:
	$(DJANGO_MANAGE) makemigrations keysmith

migration-check:
	$(DJANGO_MANAGE) makemigrations --check --dry-run keysmith

migrate-dev:
	$(DJANGO_MANAGE) migrate

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf dist build *.egg-info
