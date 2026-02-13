# django-keysmith

## Contributor Quick Start

- `make setup` to create/sync the virtualenv
- `make test` to run automated tests
- `make migration-check` to confirm model changes are captured by migrations

Tests run with `pytest` against lightweight `tests.settings` and SQLite, so
contributors do not need to start a Django server for normal library validation.

## Migration Workflow (Library Development)

This repository includes a minimal Django project under `dev/` used only for
generating and validating migrations for the `keysmith` app.

Use:

- `make makemigrations` to generate new migration files for `keysmith`
- `make migration-check` to ensure no model changes are missing migrations
- `make migrate-dev` to apply migrations to the local dev SQLite database

The dev project settings live in `dev/settings.py` and are intentionally minimal.

## Optional DRF Integration

The base dev/test setup does not require Django REST Framework. If you want to
exercise DRF endpoints in `dev/tokenlab`, install extras and run the dev server:

- `uv sync --dev --extra drf`
- `uv run python dev/manage.py runserver`
