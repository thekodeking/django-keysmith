# Settings

All configuration lives in a single `KEYSMITH` dictionary in `settings.py`. Unspecified keys use library defaults. Unknown keys trigger warning `keysmith.W002`.

```python
KEYSMITH = {
    "DEFAULT_EXPIRY_DAYS": 90,
    "ENABLE_AUDIT_LOGGING": True,
}
```

Settings reload automatically when Django's `setting_changed` signal fires (useful in tests).

Access defaults programmatically:

```python
from keysmith.settings import KEYSMITH_DEFAULTS, keysmith_settings
```

---

## Hashing {#hashing}

| Key | Default | Description |
| --- | --- | --- |
| `HASH_BACKEND` | `keysmith.hashers.PBKDF2SHA512TokenHasher` | Dotted path to hasher class |
| `HASH_ITERATIONS` | `100_000` | PBKDF2 iterations (minimum 10,000) |

---

## Token generation {#token-generation}

| Key | Default | Description |
| --- | --- | --- |
| `TOKEN_PREFIX` | `"tok"` | Namespace in public tokens (max 246 chars) |
| `TOKEN_SECRET_LENGTH` | `32` | Secret length (minimum 16) |
| `DEFAULT_EXPIRY_DAYS` | `90` | Default lifetime in days. Falsy value → no default expiry. |

---

## Request authentication {#request-authentication}

| Key | Default | Description |
| --- | --- | --- |
| `HEADER_NAME` | `HTTP_X_KEYSMITH_TOKEN` | `request.META` key (= `X-KEYSMITH-TOKEN` header) |
| `ALLOW_QUERY_PARAM` | `False` | Accept token via query string |
| `QUERY_PARAM_NAME` | `keysmith_token` | Query parameter name |
| `TRUST_PROXIES` | `False` | Read client IP from `X-Forwarded-For` |

---

## Scopes {#scopes}

| Key | Default | Description |
| --- | --- | --- |
| `AVAILABLE_SCOPES` | `[]` | Allowlist of codenames. Empty = no restriction. |
| `DEFAULT_SCOPES` | `[]` | Applied when `create_token(scopes=None)` |

---

## Models {#models}

| Key | Default | Description |
| --- | --- | --- |
| `TOKEN_MODEL` | `keysmith.Token` | Swappable token model |
| `AUDIT_LOG_MODEL` | `keysmith.TokenAuditLog` | Swappable audit model |

---

## Audit logging {#audit-logging}

| Key | Default | Description |
| --- | --- | --- |
| `ENABLE_AUDIT_LOGGING` | `True` | Master switch |
| `AUDIT_LOG_HOOK` | `None` | Callable replacing DB write |
| `AUDIT_LOG_RETENTION_DAYS` | `None` | Default for `prune_audit_logs` |

---

## Hooks {#hooks}

| Key | Default | Signature |
| --- | --- | --- |
| `RATE_LIMIT_HOOK` | `None` | `hook(request, raw_token=None)` |
| `DRF_THROTTLE_HOOK` | `None` | `hook(request, token=None)` |

---

## Error messages {#error-messages}

| Key | Default | Description |
| --- | --- | --- |
| `DEFAULT_ERROR_MESSAGES` | See below | User-facing strings (lazy-translated) |

Built-in message keys:

| Key | Default text |
| --- | --- |
| `missing_token` | Authentication credentials were not provided. |
| `invalid_token` | Your session has expired or the token is invalid. |
| `insufficient_scope` | You do not have permission to perform this action. |
| `rate_limited` | Too many authentication attempts. Try again later. |

Override individual keys - unspecified keys keep their defaults:

```python
KEYSMITH = {
    "DEFAULT_ERROR_MESSAGES": {
        "invalid_token": "API token is invalid or expired.",
    },
}
```

---

## Production example

```python
KEYSMITH = {
    "HASH_ITERATIONS": 150_000,
    "DEFAULT_EXPIRY_DAYS": 60,
    "HEADER_NAME": "HTTP_X_API_TOKEN",
    "ALLOW_QUERY_PARAM": False,
    "ENABLE_AUDIT_LOGGING": True,
    "AUDIT_LOG_RETENTION_DAYS": 90,
    "TRUST_PROXIES": True,
    "TOKEN_PREFIX": "api",
    "TOKEN_SECRET_LENGTH": 40,
    "AVAILABLE_SCOPES": ["read", "write", "admin"],
    "DEFAULT_ERROR_MESSAGES": {
        "invalid_token": "API token is invalid or expired.",
    },
}
```

---

**See also:** [Customization](../extending/customization.md) · [Security](../extending/security.md)
