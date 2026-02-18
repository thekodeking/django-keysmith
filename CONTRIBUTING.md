# Contributing to django-keysmith

Thanks for contributing.

## Prerequisites

- Python 3.9+
- `uv` installed

## Local setup

```bash
make setup
```

If you are working on DRF-related behavior:

```bash
uv sync --dev --extra drf
```

## Development workflow

1. Create a branch from `main`.
2. Make focused, atomic changes.
3. Run checks locally.
4. Open a pull request with context and test evidence.

## Required checks before PR

```bash
make lint
make test
make migration-check
```

If docs changed, validate docs locally:

```bash
make docs-serve
```

If you changed model definitions, include migration files and ensure `make migration-check` passes.

## Testing strategy

- Canonical test entrypoint: `runtests.py`
- Django management commands for package validation: `tests/manage.py`
- Tests are organized by feature area (authentication, DRF integration, models, etc.)
- All tests use `pytest` with `pytest-django`

## Pull request expectations

- Include motivation and design notes
- Include behavioral impact and migration notes
- Add/update tests for changed behavior
- Keep docs current (`README.md` and `docs/*`)

## Release hygiene

- Avoid breaking public APIs without a deprecation path
- Document security-relevant behavior changes
- Keep defaults safe

## Reporting security issues

Please follow `SECURITY.md`.
