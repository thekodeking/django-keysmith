# Configuration

Configure Keysmith through the `KEYSMITH` dictionary in Django settings. Most projects start with defaults and then tighten behavior around expiry, scopes, and error messaging.

## Minimal Configuration

This baseline enables default expiry and audit logging behavior explicitly.

```python
KEYSMITH = {
    "DEFAULT_EXPIRY_DAYS": 90,
    "ENABLE_AUDIT_LOGGING": True,
}
```

## Settings Reference

The table below lists the settings used by Keysmith services, middleware, and DRF integration.

| Setting | Default | Purpose |
| --- | --- | --- |
| `HASH_BACKEND` | `keysmith.hashers.PBKDF2SHA512TokenHasher` | Token hasher class |
| `HASH_ITERATIONS` | `100_000` | PBKDF2 iteration count |
| `DEFAULT_EXPIRY_DAYS` | `90` | Default token lifetime in days |
| `AVAILABLE_SCOPES` | `[]` | Allowed scope codenames for token assignment |
| `DEFAULT_SCOPES` | `[]` | Scope codenames applied when scopes are omitted |
| `TOKEN_MODEL` | `keysmith.Token` | Token model path |
| `AUDIT_LOG_MODEL` | `keysmith.TokenAuditLog` | Audit log model path |
| `HEADER_NAME` | `HTTP_X_KEYSMITH_TOKEN` | Django `request.META` key for token header |
| `ALLOW_QUERY_PARAM` | `False` | Allow token in query string |
| `QUERY_PARAM_NAME` | `keysmith_token` | Query parameter name |
| `ENABLE_AUDIT_LOGGING` | `True` | Enable audit writes |
| `TOKEN_PREFIX` | `tok` | Prefix namespace for new tokens |
| `TOKEN_SECRET_LENGTH` | `32` | Secret length used for new tokens |
| `HINT_LENGTH` | `8` | Max hint length stored on token |
| `RATE_LIMIT_HOOK` | `None` | Hook path: `hook(request, raw_token=None)` |
| `DRF_THROTTLE_HOOK` | `None` | Hook path: `hook(request, token=None)` |
| `DEFAULT_ERROR_MESSAGES` | built-in map | Error text overrides |

## Scope Validation Behavior

Scope-related settings are enforced during token creation. This helps prevent accidental privilege expansion when teams create tokens from multiple code paths.

- If `AVAILABLE_SCOPES` is set, Keysmith rejects requested/default scopes outside that allowlist.
- `DEFAULT_SCOPES` is only applied when `create_token(..., scopes=...)` is omitted.

## Hook Contracts

Hooks are loaded through `import_string` and should raise controlled exceptions only when you intentionally want to block access.

`RATE_LIMIT_HOOK` runs in middleware before token authentication:

```python
def rate_limit_hook(request, raw_token=None):
    return None
```

`DRF_THROTTLE_HOOK` runs in DRF after token authentication:

```python
def drf_throttle_hook(request, token=None):
    return None
```

## Production Example

Use stricter values for production, especially for hash cost and token lifetimes.

```python
KEYSMITH = {
    "HASH_ITERATIONS": 150_000,
    "DEFAULT_EXPIRY_DAYS": 60,
    "HEADER_NAME": "HTTP_X_API_TOKEN",
    "ALLOW_QUERY_PARAM": False,
    "ENABLE_AUDIT_LOGGING": True,
    "TOKEN_PREFIX": "api",
    "TOKEN_SECRET_LENGTH": 40,
    "HINT_LENGTH": 8,
    "DEFAULT_ERROR_MESSAGES": {
        "invalid_token": "API token is invalid or expired.",
        "insufficient_scope": "Token does not have required scope.",
    },
}
```
