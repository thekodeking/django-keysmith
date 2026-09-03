# django-keysmith

<p align="center">
  <img src="https://img.shields.io/pypi/v/django-keysmith.svg" alt="PyPI version">
  <img src="https://img.shields.io/pypi/pyversions/django-keysmith.svg" alt="Python versions">
  <img src="https://img.shields.io/badge/django-4.2%2B-blue.svg" alt="Django versions">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

Production-oriented API token management for Django and Django REST Framework.

## What is Keysmith?

Keysmith treats API tokens as first-class database records with explicit lifecycle operations, hashed storage, and request-level audit events. Instead of scattering credential logic across your codebase, you get a cohesive system for creating, rotating, revoking, and auditing machine credentials.

**The problem:** Static API keys in environment variables work until they don't. Rotation means redeploying. Revocation means grep-and-replace. Audit trails mean building logging yourself.

**The solution:** Keysmith provides those pieces as a cohesive package so your team spends time on product code, not credential plumbing.

## Features

- **Secure storage** — PBKDF2-SHA512 hashing by default. Raw tokens shown once at creation, never stored.
- **Full lifecycle** — Create, rotate, revoke, and purge tokens with explicit service functions.
- **Scope-based auth** — Attach Django permission codenames to tokens. Works with your existing permission system.
- **Dual integrations** — Middleware + decorators for plain Django. Authentication classes for DRF. Same validation pipeline.
- **Audit trail** — Every lifecycle event and authentication attempt logged with request context (path, IP, user-agent, status code).
- **Admin interface** — Create tokens from Django admin with one-time raw token display. Bulk revoke/purge/rotate via admin actions.
- **Extensible** — Swappable token and audit models. Custom hash backends. Rate limiting and throttle hooks.
- **System checks** — Validates model contracts, settings safety, and warns about SQLite concurrency issues.

## Requirements

- Python 3.9+
- Django 4.2+
- Django REST Framework 3.15.2+ _(optional, for DRF integration)_

> **Note:** Keysmith uses `SELECT FOR UPDATE` for safe concurrent authentication. SQLite escalates this to a full table lock, which causes `OperationalError` under multi-threaded or multi-process load. Use PostgreSQL or MySQL in production.

## Installation

```bash
pip install django-keysmith
```

With DRF support:

```bash
pip install "django-keysmith[drf]"
```

## Quick Start

### 1. Configure Django

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

### 2. Run migrations

```bash
python manage.py migrate
```

### 3. Create a token

```python
from django.contrib.auth import get_user_model
from keysmith.services.tokens import create_token

User = get_user_model()
user = User.objects.get(username="api-user")

token, raw_token = create_token(
    name="local-dev",
    user=user,  # recommended for plain Django decorators
)

print(token.prefix)   # tok_a1B2c3D4
print(raw_token)      # store immediately; raw secret is not recoverable from DB
```

### 4. Protect a view

```python
from django.http import JsonResponse
from keysmith.django.decorator import keysmith_required

@keysmith_required
def secure_view(request):
    return JsonResponse({
        "ok": True,
        "token_prefix": request.keysmith_token.prefix,
    })
```

### 5. Call with header

```bash
curl -H "X-KEYSMITH-TOKEN: <raw-token>" http://localhost:8000/api/secure/
```

## DRF Integration

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

## Token Lifecycle

Keysmith provides explicit lifecycle functions for managing tokens:

```python
from keysmith.services.tokens import create_token, rotate_token, revoke_token

# Create — returns (token, raw_token)
token, raw = create_token(name="billing-worker", user=user)

# Create with options
token, raw = create_token(
    name="payment-service",
    user=user,
    description="Handles payment processing",
    scopes=[permission],           # Django Permission instances
    expires_at=expiry,             # datetime or None for no expiry
    token_type="system",           # "user" (default) or "system"
    request=request,               # optional, for audit context
)

# Rotate — invalidates previous secret, returns new raw token
new_raw = rotate_token(token, actor=request.user, request=request)

# Revoke — marks token as unusable
revoke_token(token, actor=request.user, request=request)

# Revoke + purge — soft-delete (marks as purged)
revoke_token(token, purge=True, actor=request.user, request=request)
```

**Token types:**

| Type | Use case |
| --- | --- |
| `user` | Tokens bound to a specific user (default) |
| `system` | Service-to-service tokens not tied to a user |

**Token states:**

| State | Description |
| --- | --- |
| Active | Token is valid and can authenticate requests |
| Expired | `expires_at` has passed. Token fails authentication. |
| Revoked | Explicitly disabled. Token fails authentication. |
| Purged | Soft-deleted. Token fails authentication and is hidden from active queries. |

## Scopes and Permissions

Scopes use Django's built-in permission codenames. No custom permission model required.

```python
# Create token with scopes
permission = Permission.objects.get(codename="tokens:read")
token, raw = create_token(name="readonly-client", user=user, scopes=[permission])
```

**Plain Django:**

```python
from keysmith.django.decorator import keysmith_required
from keysmith.django.permissions import keysmith_scopes

@keysmith_required
@keysmith_scopes("write")
def create_resource(request):
    ...
```

**DRF:**

```python
from keysmith.drf.permissions import HasKeysmithScopes, ScopedPermission

class MyView(APIView):
    permission_classes = [HasKeysmithScopes]
    required_scopes = ["tokens:read"]

# Or inline:
class MyView(APIView):
    permission_classes = [ScopedPermission("write")]
```

## Configuration

Configure through `KEYSMITH` in `settings.py`:

```python
KEYSMITH = {
    "DEFAULT_EXPIRY_DAYS": 90,
    "HEADER_NAME": "HTTP_X_KEYSMITH_TOKEN",
    "ALLOW_QUERY_PARAM": False,
    "ENABLE_AUDIT_LOGGING": True,
}
```

### Core Settings

| Setting | Default | Description |
| --- | --- | --- |
| `TOKEN_MODEL` | `keysmith.Token` | Swappable token model path |
| `TOKEN_PREFIX` | `tok` | Prefix namespace for generated tokens |
| `TOKEN_SECRET_LENGTH` | `32` | Generated secret length (minimum 16) |
| `DEFAULT_EXPIRY_DAYS` | `90` | Default token expiry window (null for no expiry) |
| `HASH_BACKEND` | `keysmith.hashers.PBKDF2SHA512TokenHasher` | Token hashing backend |
| `HASH_ITERATIONS` | `100_000` | PBKDF2 cost factor (minimum 10,000) |

### Authentication Settings

| Setting | Default | Description |
| --- | --- | --- |
| `HEADER_NAME` | `HTTP_X_KEYSMITH_TOKEN` | Header key in `request.META` |
| `AUTH_HEADER_TYPES` | `("Bearer", "Token")` | Accepted schemes in `Authorization` header |
| `WWW_AUTHENTICATE_SCHEME` | `"Bearer"` | Challenge scheme in `WWW-Authenticate` header (RFC 9110) |
| `ALLOW_QUERY_PARAM` | `False` | Accept token via query string |
| `QUERY_PARAM_NAME` | `keysmith_token` | Query parameter name |
| `LAST_USED_UPDATE_INTERVAL` | `60` | Minimum seconds between database writes to `last_used_at` |

### Audit Settings

| Setting | Default | Description |
| --- | --- | --- |
| `ENABLE_AUDIT_LOGGING` | `True` | Enable audit row creation |
| `AUDIT_LOG_MODEL` | `keysmith.TokenAuditLog` | Swappable audit model path |
| `AUDIT_LOG_HOOK` | `None` | Callable replacing default audit DB write |
| `AUDIT_LOG_RETENTION_DAYS` | `None` | Default for `prune_audit_logs` command |
| `TRUST_PROXIES` | `False` | Read IP from `X-Forwarded-For` header |
| `CLIENT_IP_HEADER` | `None` | Custom header for client IP (e.g. `HTTP_X_REAL_IP`, `HTTP_CF_CONNECTING_IP`) |
| `CLIENT_IP_HOOK` | `None` | Callable or dotted string `hook(request) -> str` resolving client IP |

### Scope Settings

| Setting | Default | Description |
| --- | --- | --- |
| `AVAILABLE_SCOPES` | `[]` | Allowed permission codenames |
| `DEFAULT_SCOPES` | `[]` | Auto-assigned codenames on token create |

### Extensibility Hooks

| Setting | Default | Description |
| --- | --- | --- |
| `RATE_LIMIT_HOOK` | `None` | Callable: `hook(request, raw_token=None)` |
| `DRF_THROTTLE_HOOK` | `None` | Callable: `hook(request, token=None)` |

### Custom Error Messages

Override default error messages:

```python
KEYSMITH = {
    "DEFAULT_ERROR_MESSAGES": {
        "missing_token": "Please provide an API token.",
        "invalid_token": "Your token is invalid or has expired.",
        "insufficient_scope": "You lack permission for this action.",
        "rate_limited": "Too many attempts. Slow down.",
    },
}
```

## Authentication Flow

For each request, Keysmith:
1. Reads the token from the configured header (or query string if enabled)
2. Validates format and CRC checksum
3. Looks up the token by prefix (indexed for fast lookup)
4. Checks lifecycle state (revoked, purged, expired)
5. Verifies the secret hash against the stored key
6. Updates `last_used_at` timestamp
7. Attaches auth context to the request
8. Writes the corresponding audit event

One validator (`authenticate_token`) powers both the Django middleware and the DRF authentication class.

## Token Format

```
tok_a1B2c3D4:abcdefghijklmnopqrstuvwxyz012345678901234567890123456789012654321
└── prefix ──┘ └──────────── secret (32 chars default) ────────────────┘└crc┘
```

| Part | Stored in DB? | Purpose |
| --- | --- | --- |
| Prefix (`tok_...`) | Yes, indexed | Fast lookup |
| Secret | Hash only | Verified on each request |
| CRC (6 digits) | No | Reject malformed tokens before DB hit |

## Audit Logging

Every authentication attempt and lifecycle event is logged with request context:

| Action | Description |
| --- | --- |
| `created` | Token was created |
| `rotated` | Token secret was rotated |
| `revoked` | Token was revoked or purged |
| `auth_success` | Authentication succeeded |
| `auth_failed` | Authentication failed (missing, invalid, revoked, expired, rate-limited) |

Each log entry includes: token, action, path, method, status code, IP address, user agent, and optional extra JSON.

### Prune Old Logs

```bash
python manage.py prune_audit_logs
```

Set a default retention period:

```python
KEYSMITH = {
    "AUDIT_LOG_RETENTION_DAYS": 30,
}
```

## Management Commands

| Command | Description |
| --- | --- |
| `create_token` | Create a new API token and print the one-time raw secret |
| `revoke_token` | Revoke or purge a token by prefix |
| `list_tokens` | List API tokens with status, user, prefix, and expiry |
| `prune_audit_logs` | Remove audit log entries older than retention period |

```bash
# Create a new token via CLI
python manage.py create_token --name "CI Deploy" --user admin --scopes read,write --days 90

# List tokens
python manage.py list_tokens --active

# Revoke a token by prefix
python manage.py revoke_token tok_a1b2c3d4

# Prune audit logs
python manage.py prune_audit_logs --days 30
```

## Admin Experience

Keysmith registers `Token` and `TokenAuditLog` in Django admin:

- Create tokens from admin UI
- See raw token once immediately after creation (stored in session, shown once)
- Revoke, purge, or rotate selected tokens via admin actions
- Inspect audit events by token, action, path, status, and timestamp
- Rotate individual tokens from the change form

## Extending Keysmith

### Swappable Models

```python
KEYSMITH = {
    "TOKEN_MODEL": "myapp.MyToken",
    "AUDIT_LOG_MODEL": "myapp.MyAuditLog",
}
```

Custom models must satisfy required field/method contracts (validated by Django system checks at startup).

### Custom Hash Backend

```python
KEYSMITH = {
    "HASH_BACKEND": "myapp.security.MyTokenHasher",
}
```

Hasher must implement `BaseTokenHasher.hash()` and `BaseTokenHasher.verify()`.

### Rate Limit / Throttle Hooks

```python
# settings.py
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
