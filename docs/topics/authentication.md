# Authentication

Keysmith validates a raw token string and attaches the result to the request. One function - `authenticate_token` - does all the work. Middleware and DRF are thin wrappers around it.

---

## The validation pipeline

```
Header / query param
        │
        ▼
  Parse + CRC check ──── InvalidToken (malformed)
        │
        ▼
  Lookup by prefix ───── InvalidToken (not found)
        │
        ▼
  Lifecycle checks ───── RevokedToken / ExpiredToken
        │
        ▼
  Hash verify ────────── InvalidToken (wrong secret)
        │
        ▼
  Update last_used_at
        │
        ▼
  Return Token instance
```

Steps run using optimized, non-locking reads with `select_related("user")` and `prefetch_related("scopes")`. Token usage timestamps (`last_used_at`) are updated atomically and debounced via `LAST_USED_UPDATE_INTERVAL` (default: 60s) to prevent database write amplification on read-heavy workloads.

---

## Where tokens are read from

Clients can send the token using the standard `Authorization` header:

```http
Authorization: Bearer tok_a1B2c3D4:secret...crc
```

Or using the configured custom header:

```http
X-KEYSMITH-TOKEN: tok_a1B2c3D4:secret...crc
```

Django exposes this as `request.META["HTTP_X_KEYSMITH_TOKEN"]`.

| Setting | Default | Effect |
| --- | --- | --- |
| `HEADER_NAME` | `HTTP_X_KEYSMITH_TOKEN` | Which `META` key to read |
| `ALLOW_QUERY_PARAM` | `False` | Also accept `?keysmith_token=…` |
| `QUERY_PARAM_NAME` | `keysmith_token` | Query parameter name |

!!! warning
    Query-string tokens appear in access logs and browser history. Keep `ALLOW_QUERY_PARAM` disabled in production unless you have no alternative.

---

## Integration points

### Middleware (Django views)

Runs on every request. Sets three attributes:

```python
request.keysmith_token      # Token or None
request.keysmith_user       # token.user or None
request.keysmith_auth_error # TokenAuthError subclass or None
```

Middleware never returns 401. Views enforce authentication with `@keysmith_required`.

After the response, middleware writes `auth_success` or `auth_failed` audit events - but only for views decorated with `@keysmith_required`.

### DRF authentication class

`KeysmithAuthentication` plugs into DRF's auth flow:

- `request.auth` → the `Token` instance
- `request.user` → `token.user`, or DRF's unauthenticated user placeholder when no user is linked

Missing token → returns `None` (DRF continues to other auth classes).
`TokenAuthError` → raises `AuthenticationFailed` with the configured `invalid_token` message.

When both middleware and DRF are active, DRF sets `_keysmith_skip_middleware_audit` to prevent duplicate audit rows.

---

## Exceptions

```text
TokenAuthError
├── InvalidToken    malformed, missing, unknown prefix, hash mismatch
├── RevokedToken    revoked=True or purged=True
└── ExpiredToken    past expires_at
```

Use these for **internal** logging. External clients should always see a generic error - see [Security](../extending/security.md#error-disclosure).

### Direct usage

```python
from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import InvalidToken, ExpiredToken, RevokedToken

try:
    token = authenticate_token(raw_token)
except (InvalidToken, ExpiredToken, RevokedToken) as exc:
    log_internally(exc)
    return generic_401()
```

---

## Rate limiting

`RATE_LIMIT_HOOK` runs in middleware **before** `authenticate_token`:

```python
KEYSMITH = {
    "RATE_LIMIT_HOOK": "myapp.hooks.rate_limit",
}
```

```python
def rate_limit(request, raw_token=None):
    if too_many_attempts(request):
        raise RateLimitExceeded()
```

`DRF_THROTTLE_HOOK` runs **after** successful DRF authentication. It can raise DRF's `Throttled` exception.

---

**See also:** [Django integration](../integrations/django.md) · [DRF integration](../integrations/drf.md) · [Authentication reference](../reference/authentication.md)
