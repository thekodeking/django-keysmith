# Install

## Requirements

| Dependency | Version |
| --- | --- |
| Python | 3.9+ |
| Django | 4.2+ |
| DRF *(optional)* | 3.15.2+ |

## Install the package

=== "Django only"

    ```bash
    pip install django-keysmith
    ```

=== "With DRF"

    ```bash
    pip install "django-keysmith[drf]"
    ```

## Add to Django

**1. Register the app**

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "keysmith",
]
```

**2. Add middleware**

Place `KeysmithAuthenticationMiddleware` immediately after Django's `AuthenticationMiddleware`:

```python
MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
]
```

The middleware extracts tokens and attaches context to every request. It does not block unauthenticated traffic - views opt in via `@keysmith_required` or DRF permission classes.

**3. Run migrations**

```bash
python manage.py migrate
```

Keysmith creates two tables: `keysmith_token` and `keysmith_token_audit_log`.

## Optional: DRF defaults

Skip this if you only use plain Django views.

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "keysmith.drf.auth.KeysmithAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "keysmith.drf.permissions.RequireKeysmithToken",
    ],
}
```

## Verify

```bash
python manage.py shell
```

```python
from keysmith.services.tokens import create_token

token, raw = create_token(name="smoke-test")
print(token.prefix)
print(raw)
```

!!! warning "Save the raw token"
    The string returned as `raw` is the only copy of the secret. The database stores a hash.

## System checks

Keysmith registers Django system checks that run on `manage.py check`:

| ID | Level | What it catches |
| --- | --- | --- |
| `keysmith.E001`–`E003` | Error | Swappable model contract violations |
| `keysmith.E004`–`E007` | Error | Invalid `TOKEN_PREFIX`, `TOKEN_SECRET_LENGTH`, or `HASH_ITERATIONS` |
| `keysmith.W001` | Warning | SQLite as default database (concurrency) |
| `keysmith.W002` | Warning | Unknown keys in `KEYSMITH` settings |

---

**Next:** [Tutorial](tutorial.md) - create a token and make your first authenticated request.
