PYTHON := uv run python
PIP    := uv pip

PACKAGE := keysmith

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
	uv run python -m build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf dist build *.egg-info
