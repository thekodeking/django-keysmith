# django-keysmith

<p align="center">
  <img src="https://img.shields.io/pypi/v/django-keysmith.svg" alt="PyPI version">
  <img src="https://img.shields.io/pypi/pyversions/django-keysmith.svg" alt="Python versions">
  <img src="https://img.shields.io/badge/django-4.0%2B-blue.svg" alt="Django versions">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

Production-oriented API token management for Django and Django REST Framework.

`django-keysmith` gives you a lifecycle-first token system with secure secret storage, rotation and revocation primitives, scope-based authorization, and built-in audit trails.

## Why Keysmith

Many token solutions cover basic request authentication but leave lifecycle operations, observability, and extension points to app-level glue code. Keysmith provides those pieces as a cohesive package:

- secure token generation and hashed storage
- explicit lifecycle APIs (`create`, `rotate`, `revoke`)
- plain Django and DRF integration on one validation pipeline
- structured audit records for auth and lifecycle events

## Features

- No plaintext token storage (PBKDF2-SHA512 by default)
- Deterministic lookup path (`prefix` index + hash verify)
- Token states: active, expired, revoked, purged
- Scope model backed by Django `auth.Permission` codenames
- Middleware + decorators for plain Django
- Authentication + permission classes for DRF
- One-time raw token display in Django admin create flow
- Extensibility hooks for rate limiting and DRF throttling
- Swappable token and audit models with system-contract checks

## Requirements

- Python 3.9+
- Django 4.0+

Optional:

- Django REST Framework 3.15.2+ (`django-keysmith[drf]`)

## Installation

```bash
pip install django-keysmith
```

With DRF support:

```bash
pip install "django-keysmith[drf]"
```

## Quick Start (Plain Django)

1. Add Keysmith to your app and middleware stack.

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "keysmith",
]

MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
]
```

2. Run migrations.

```bash
python manage.py migrate
```

3. Create a token and keep the raw value safe.

```python
from django.contrib.auth import get_user_model
from keysmith.services.tokens import create_token

User = get_user_model()
user = User.objects.get(username="api-user")

token, raw_token = create_token(
    name="local-dev",
    user=user,  # recommended for plain Django decorators
)

print(token.prefix)
print(raw_token)  # store immediately; raw secret is not recoverable from DB
```

4. Protect views.

```python
from django.http import JsonResponse
from keysmith.django.decorator import keysmith_required

@keysmith_required
def secure_view(request):
    return JsonResponse({"ok": True, "token_prefix": request.keysmith_token.prefix})
```

5. Call with header:

```bash
curl -H "X-KEYSMITH-TOKEN: <raw-token>" http://localhost:8000/api/secure/
```

## Quick Start (DRF)

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "keysmith.drf.auth.KeysmithAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "keysmith.drf.permissions.RequireKeysmithToken",
    ],
}
```

```python
from rest_framework.response import Response
from rest_framework.views import APIView

class StatusView(APIView):
    def get(self, request):
        return Response({
            "authenticated": True,
            "token_prefix": request.auth.prefix,
        })
```

## Token Lifecycle API

```python
from keysmith.services.tokens import create_token, rotate_token, revoke_token

# create
token, raw = create_token(name="billing-worker", user=user)

# rotate (invalidates previous raw token immediately)
new_raw = rotate_token(token, actor=request.user, request=request)

# revoke (optionally purge)
revoke_token(token, purge=True, actor=request.user, request=request)
```

## Authentication Flow

For each request, Keysmith reads the token from the configured header, validates format and checksum, resolves the token by prefix, enforces lifecycle checks (revoked, purged, expired), verifies the secret hash, marks the token as used, attaches auth context to the request, and writes the corresponding audit event.

## Public Token Format

Example:

```text
tok_ab12CD34:SecretValueHere123456
```

Structure:

- `<namespace>_<identifier>`: indexed prefix used for lookup
- `:<secret>`: verified against hashed `key` in DB
- trailing `6-digit CRC`: format integrity check

## Configuration

Configure through `KEYSMITH` in `settings.py`.

```python
KEYSMITH = {
    "DEFAULT_EXPIRY_DAYS": 90,
    "ENABLE_AUDIT_LOGGING": True,
    "HEADER_NAME": "HTTP_X_KEYSMITH_TOKEN",
    "ALLOW_QUERY_PARAM": False,
}
```

Common options:

| Setting | Default | Purpose |
| --- | --- | --- |
| `HASH_BACKEND` | `keysmith.hashers.PBKDF2SHA512TokenHasher` | Token hashing backend |
| `HASH_ITERATIONS` | `100_000` | PBKDF2 cost factor |
| `DEFAULT_EXPIRY_DAYS` | `90` | Default token expiry window |
| `TOKEN_MODEL` | `keysmith.Token` | Swappable token model |
| `AUDIT_LOG_MODEL` | `keysmith.TokenAuditLog` | Swappable audit model |
| `HEADER_NAME` | `HTTP_X_KEYSMITH_TOKEN` | Header key in `request.META` |
| `ALLOW_QUERY_PARAM` | `False` | Accept token via query string |
| `QUERY_PARAM_NAME` | `keysmith_token` | Query parameter name |
| `ENABLE_AUDIT_LOGGING` | `True` | Enable audit row creation |
| `TOKEN_PREFIX` | `tok` | Prefix namespace |
| `TOKEN_SECRET_LENGTH` | `32` | Generated secret length |
| `HINT_LENGTH` | `8` | Stored hint length |
| `AVAILABLE_SCOPES` | `[]` | Allowed permission codenames |
| `DEFAULT_SCOPES` | `[]` | Auto-assigned codenames on token create |
| `RATE_LIMIT_HOOK` | `None` | Callable: `hook(request, raw_token=None)` |
| `DRF_THROTTLE_HOOK` | `None` | Callable: `hook(request, token=None)` |

## Scopes and Permissions

Scopes are Django permission codenames attached to each token.

- Plain Django: use `@keysmith_scopes("write")`
- DRF: use `HasKeysmithScopes` or `ScopedPermission("write")`

```python
from keysmith.django.decorator import keysmith_required
from keysmith.django.permissions import keysmith_scopes

@keysmith_required
@keysmith_scopes("write")
def create_resource(request):
    ...
```

## Admin Experience

Keysmith registers `Token` and `TokenAuditLog` in Django admin:

- create tokens from admin UI
- see raw token once immediately after creation
- revoke/purge selected tokens via admin actions
- inspect audit events by token, action, path, status, and timestamp

## Extending Keysmith

### Swappable models

```python
KEYSMITH = {
    "TOKEN_MODEL": "myapp.MyToken",
    "AUDIT_LOG_MODEL": "myapp.MyAuditLog",
}
```

Custom models must satisfy required field/method contracts (validated by Django system checks).

### Custom hash backend

```python
KEYSMITH = {
    "HASH_BACKEND": "myapp.security.MyTokenHasher",
}
```

Hasher must implement `BaseTokenHasher.hash()` and `BaseTokenHasher.verify()`.

### Rate limit / throttle hooks

```python
KEYSMITH = {
    "RATE_LIMIT_HOOK": "myapp.auth.rate_limit_hook",
    "DRF_THROTTLE_HOOK": "myapp.auth.drf_throttle_hook",
}
```

## Development

```bash
make setup
make lint
make test
make migration-check
```

Build or preview docs:

```bash
make docs-build
make docs-serve
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Please report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
