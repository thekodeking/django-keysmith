# Authentication

---

## `authenticate_token`

```python
from keysmith.auth.base import authenticate_token

authenticate_token(raw_token: str) -> Token
```

**Stages:**

1. Non-empty check
2. Parse public token + CRC verification
3. `SELECT … FOR UPDATE` by `prefix`
4. `revoked` / `purged` / `is_expired` checks
5. Hash verification via configured `HASH_BACKEND`
6. `mark_token_used()`

**Exceptions** (all inherit `TokenAuthError`):

```python
from keysmith.auth.exceptions import InvalidToken, ExpiredToken, RevokedToken
```

---

## `get_message`

```python
from keysmith.auth.utils import get_message

get_message(key: str, *, default: str | None = None) -> str
```

Returns a string from `DEFAULT_ERROR_MESSAGES`. Keys: `missing_token`, `invalid_token`, `insufficient_scope`, `rate_limited`.

---

## `KeysmithAuthenticationMiddleware`

```python
from keysmith.django.middleware import KeysmithAuthenticationMiddleware
```

**Sets on request:**

| Attribute | When |
| --- | --- |
| `keysmith_token` | Successful auth |
| `keysmith_user` | `token.user` if set |
| `keysmith_auth_error` | On `TokenAuthError` |
| `_keysmith_auth_required` | Set by `@keysmith_required` |

**Hooks:** `RATE_LIMIT_HOOK` before auth.

**Audit:** post-response `auth_success` / `auth_failed` for `@keysmith_required` views.

---

## `keysmith_required`

```python
from keysmith.django.decorator import keysmith_required
```

```python
@keysmith_required
def view(request): ...

@keysmith_required(allow_anonymous=False, missing_message=None, invalid_message=None)
def view(request): ...
```

Returns `HttpResponseUnauthorized` (401) on failure.

---

## `HttpResponseUnauthorized`

```python
from keysmith.django.http import HttpResponseUnauthorized
```

Subclass of `HttpResponse` with `status_code = 401`.

---

## `KeysmithAuthentication`

```python
from keysmith.drf.auth import KeysmithAuthentication
```

DRF `BaseAuthentication` subclass.

| Input | Result |
| --- | --- |
| No token | `None` |
| `TokenAuthError` | `AuthenticationFailed` |
| `Throttled` from hook | Re-raised after audit |
| Success | `(user, token)` |

Reads header via `request.headers` (converts `HTTP_X_KEYSMITH_TOKEN` → `X-KEYSMITH-TOKEN`).

Sets `_keysmith_skip_middleware_audit` on underlying Django request.

---

## Token utilities

Module: `keysmith.utils.tokens`

```python
from keysmith.utils.tokens import (
    PublicToken,
    build_public_token,
    compute_crc,
    extract_prefix_and_secret,
    generate_raw_secret,
)
```

| Function | Purpose |
| --- | --- |
| `build_public_token(namespace, identifier, secret)` | Build `{ns}_{id}:{secret}{crc}` |
| `extract_prefix_and_secret(public_token)` | Parse and validate; raises `ValueError` |
| `generate_raw_secret(length=32)` | Cryptographic alphanumeric string |
| `compute_crc(value, crc_digits=6)` | CRC32 checksum, zero-padded |
