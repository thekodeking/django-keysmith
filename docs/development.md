# Development

This page covers the common local workflow for contributing to Keysmith.

## Local Setup

Use the provided make target to create a virtual environment and install dependencies from the lockfile.

```bash
make setup
```

If the environment already exists:

```bash
make sync
```

## Common Commands

These are the commands you will run most often while iterating on features.

- `make test` - run the test suite
- `make lint` - run Ruff checks
- `make format` - format code
- `make check` - run lint + tests
- `make docs-serve` - serve docs with zensical
- `make docs-build` - build docs with zensical

## Migrations

When model contracts change, keep migrations synchronized with the test project.

```bash
make makemigrations
make migration-check
make migrate
```

## Pull Request Expectations

PRs are expected to preserve behavior and keep docs aligned with code changes.

- keep tests green
- update docs for behavior changes
- keep changelog entries current when shipping user-visible changes

See
[CONTRIBUTING.md](https://github.com/thekodeking/django-keysmith/blob/main/CONTRIBUTING.md)
for contributor workflow details.
