# Authentication API Reference

Technical reference for authentication functions, middleware, decorators, and exceptions.

---

## `authenticate_token`

Module: `keysmith.auth.base`

```python
from keysmith.auth.base import authenticate_token

token = authenticate_token(raw_token: str) -> Token
```

### Execution Steps

1. **Format & Non-Empty Check**: Ensures token string follows `<prefix>:<secret>` convention.
2. **CRC32 Checksum Validation**: Computes and validates the checksum in memory. Fails fast with zero database overhead if forged or malformed.
3. **Optimized DB Read**: Queries `Token.objects.select_related("user").prefetch_related("scopes").get(prefix=prefix)`. No row locks (`select_for_update`) are acquired.
4. **Lifecycle State Checks**: Validates `token.revoked is False`, `token.purged is False`, and `token.expires_at > timezone.now()`.
5. **Constant-Time Hash Verification**: Verifies `hasher.verify(secret, token.key)` using timing-safe comparisons.
6. **Debounced Activity Update**: Calls `mark_token_used()`, writing to the database only if `LAST_USED_UPDATE_INTERVAL` has elapsed.

### Exceptions Raised

All authentication exceptions inherit from `keysmith.auth.exceptions.TokenAuthError`:

```python
from keysmith.auth.exceptions import (
    TokenAuthError,
    InvalidToken,
    ExpiredToken,
    RevokedToken,
)
```

---

## `KeysmithAuthenticationMiddleware`

Module: `keysmith.django.middleware`

```python
from keysmith.django.middleware import KeysmithAuthenticationMiddleware
```

Extracts credentials from incoming requests and attaches diagnostic attributes to the `request` object.

### Request Context Attributes Set

| Attribute | When Populated | Description |
| :--- | :--- | :--- |
| `request.keysmith_token` | Successful authentication | The verified `Token` instance. |
| `request.keysmith_user` | Successful authentication | Linked Django `User` object (or `None` for system tokens). |
| `request.keysmith_auth_error` | Authentication failure | Contains the `TokenAuthError` exception instance. |

---

## `keysmith_required`

Module: `keysmith.django.decorator`

Decorator to enforce authentication on Django function-based views.

```python
from keysmith.django.decorator import keysmith_required

@keysmith_required
def my_api_view(request):
    ...
```

If the request lacks a token or the token is invalid/expired/revoked, the decorator halts execution and returns an HTTP `401 Unauthorized` JSON response.

---

## `KeysmithAuthentication`

Module: `keysmith.drf.auth`

Django REST Framework authentication class.

```python
from keysmith.drf.auth import KeysmithAuthentication
```

### Behavior

- Reads credentials from `Authorization: Bearer <token>`, `Authorization: Token <token>`, or configured `HEADER_NAME`.
- On success: Returns `(token.user, token)` tuple where `request.user` is the linked user and `request.auth` is the `Token` instance.
- On error: Raises DRF `AuthenticationFailed` (HTTP 401).
- Emits RFC 9110 challenge: `WWW-Authenticate: Bearer realm="api"`.
