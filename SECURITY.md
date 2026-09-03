# Security Policy

## Supported Versions

`django-keysmith` supports active and LTS Python and Django releases:

| Version Category | Supported Range |
| :--- | :--- |
| **Python** | `>= 3.10` (Python 3.10, 3.11, 3.12, 3.13) |
| **Django** | `4.2 LTS`, `5.1`, `5.2 LTS` (`>= 4.2, < 6.0`) |
| **Django REST Framework** | `>= 3.15` (optional) |

Security fixes for `django-keysmith` itself are applied to the latest release line.

## Dependency Security & Shared Responsibility

`django-keysmith` is designed as a reusable library. To prevent dependency resolution conflicts in your projects:

1. **Abstract Dependencies**: `django-keysmith` declares broad dependency ranges based on API compatibility (e.g. `django>=4.2,<6.0`), rather than pinning specific patch releases.
2. **Downstream Responsibility**: As an application developer using `django-keysmith`, you are responsible for pinning and applying security patch releases of Django, DRF, and transitive dependencies in your application's lockfile (`uv.lock`, `poetry.lock`, or `requirements.txt`).
3. **Automated Auditing**: We recommend running security audit tooling in your downstream CI/CD pipelines:
   - `pip-audit` (`uvx pip-audit` or `pip-audit -r requirements.txt`)
   - GitHub Dependabot or Renovate for automated dependency security advisories

## Reporting a Vulnerability

Please do not open public GitHub issues for suspected vulnerabilities.

Email: `nkrishnaraj.developer@gmail.com`

Include:
- Affected versions and environments (Python, Django, DRF)
- Detailed reproduction steps or proof-of-concept
- Expected security impact

You can expect an initial response within 72 hours.
