# Authentication API

This page documents the authentication primitives used by Keysmith across middleware and DRF.

## Core Function

`authenticate_token` is the core validator and should be treated as the canonical auth path.

```python
from keysmith.auth.base import authenticate_token
```

```python
authenticate_token(raw_token: str)
```

Validation stages:

1. non-empty token check
2. parse + checksum verification
3. token lookup by prefix (with row lock)
4. lifecycle checks (`revoked`, `purged`, `is_expired`)
5. hash verification
6. `last_used_at` update

Raises:

- `keysmith.auth.exceptions.InvalidToken`
- `keysmith.auth.exceptions.ExpiredToken`
- `keysmith.auth.exceptions.RevokedToken`

## DRF Authentication Class

Use the DRF class to plug Keysmith into DRF's authentication/permission flow.

```python
from keysmith.drf.auth import KeysmithAuthentication
```

Behavior summary:

- reads token from configured header
- calls `authenticate_token()`
- optionally runs `DRF_THROTTLE_HOOK`
- logs auth success/failure events
- returns `(request_user, token)` where `request_user` is `token.user` when present,
  otherwise DRF's configured unauthenticated user object

## Django Middleware

Use middleware for plain Django views that need token context on request.

```python
from keysmith.django.middleware import KeysmithAuthenticationMiddleware
```

Attaches request context:

- `request.keysmith_token`
- `request.keysmith_user`
- `request.keysmith_auth_error`

Also emits `auth_failed` when a `@keysmith_required` endpoint is accessed without token.

## Decorator

The decorator is the high-level plain Django view guard.

```python
from keysmith.django.decorator import keysmith_required
```

```python
keysmith_required(
    view_func=None,
    *,
    allow_anonymous: bool = False,
    missing_message: str | None = None,
    invalid_message: str | None = None,
)
```

Use for plain Django view protection.
