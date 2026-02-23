PYTHON := uv run python
PIP    := uv pip

PACKAGE := keysmith
DJANGO_TEST_MANAGE := uv run python tests/manage.py

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
	@echo "make migrate        Apply migrations using test settings"
	@echo "make docs-serve     Serve docs locally with zensical"
	@echo "make docs-build     Build docs site with zensical"
	@echo ""

setup:
	uv venv
	uv sync --dev

sync:
	uv sync --dev

test:
	uv run python runtests.py

lint:
	uv run ruff check .

format:
	uv run ruff format $(PACKAGE)

check: lint test

build:
	uv build

makemigrations:
	$(DJANGO_TEST_MANAGE) makemigrations keysmith

migration-check:
	$(DJANGO_TEST_MANAGE) makemigrations --check --dry-run keysmith

migrate:
	$(DJANGO_TEST_MANAGE) migrate

docs-serve:
	uv run --extra docs zensical serve

docs-build:
	uv run --extra docs zensical build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf dist build *.egg-info
