# django-keysmith

## Migration Workflow (Library Development)

This repository includes a minimal Django project under `dev/` used only for
generating and validating migrations for the `keysmith` app.

Use:

- `make makemigrations` to generate new migration files for `keysmith`
- `make migration-check` to ensure no model changes are missing migrations
- `make migrate-dev` to apply migrations to the local dev SQLite database

The dev project settings live in `dev/settings.py` and are intentionally minimal.
