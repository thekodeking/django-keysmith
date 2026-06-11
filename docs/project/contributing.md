# Contributing

Thanks for your interest in improving django-keysmith.

---

## Development setup

```bash
make setup    # create venv + install deps
make sync     # refresh deps from lockfile
```

## Commands

| Command | Purpose |
| --- | --- |
| `make test` | Run test suite |
| `make lint` | Ruff checks |
| `make format` | Auto-format |
| `make check` | Lint + tests |
| `make docs-serve` | Preview docs locally |
| `make docs-build` | Build static site |
| `make makemigrations` | Generate keysmith migrations |
| `make migration-check` | Verify migrations are up to date |
| `make migrate` | Apply migrations (test project) |

## Documentation

Docs are built with [Zensical](https://zensical.org/). Source lives in `docs/`, configuration in `zensical.toml`.

```bash
make docs-serve   # http://127.0.0.1:8000
make docs-build   # output in site/
```

Update docs alongside code changes. The site follows a tutorial → topics → reference structure.

## Pull requests

- Keep tests green (`make check`)
- Update docs for behavior changes
- Add changelog entries for user-visible changes

Full workflow: [CONTRIBUTING.md](https://github.com/thekodeking/django-keysmith/blob/main/CONTRIBUTING.md)

Code of conduct: [CODE_OF_CONDUCT.md](https://github.com/thekodeking/django-keysmith/blob/main/CODE_OF_CONDUCT.md)

## Security

Do not open public issues for vulnerabilities. See [SECURITY.md](https://github.com/thekodeking/django-keysmith/blob/main/SECURITY.md).
