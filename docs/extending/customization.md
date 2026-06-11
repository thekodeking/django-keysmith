# Customization

Keysmith is designed to be extended without forking. Swap models, hashers, and hooks through settings.

---

## Swappable models

```python
KEYSMITH = {
    "TOKEN_MODEL": "myapp.MyToken",
    "AUDIT_LOG_MODEL": "myapp.MyAuditLog",
}
```

Subclass the abstract bases:

```python
from keysmith.models.base import AbstractToken, AbstractTokenAuditLog


class MyToken(AbstractToken):
    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE)

    class Meta(AbstractToken.Meta):
        db_table = "my_token"


class MyAuditLog(AbstractTokenAuditLog):
    class Meta(AbstractTokenAuditLog.Meta):
        db_table = "my_audit_log"
```

Django system checks (`keysmith.E001`–`E003`) validate required fields and methods at startup. See [Models reference](../reference/models.md#swappable-models).

Use `get_token_model()` and `get_audit_log_model()` in your code instead of importing concrete models directly.

---

## Custom hash backend

```python
KEYSMITH = {
    "HASH_BACKEND": "myapp.security.FastTokenHasher",
}
```

Implement `keysmith.hashers.base.BaseTokenHasher`:

```python
from keysmith.hashers.base import BaseTokenHasher


class FastTokenHasher(BaseTokenHasher):
    def hash(self, secret: str) -> str:
        ...

    def verify(self, secret: str, hashed: str) -> bool:
        ...
```

The default `PBKDF2SHA512TokenHasher` uses Django's `PBKDF2PasswordHasher` with `algorithm="pbkdf2_sha512"` and `iterations=HASH_ITERATIONS`.

---

## Hooks

Hooks are loaded via `import_string` from dotted paths in settings.

### Rate limit (middleware)

```python
KEYSMITH = {"RATE_LIMIT_HOOK": "myapp.hooks.rate_limit"}
```

```python
def rate_limit(request, raw_token=None):
    """Called before authenticate_token. Raise to block."""
```

### DRF throttle

```python
KEYSMITH = {"DRF_THROTTLE_HOOK": "myapp.hooks.drf_throttle"}
```

```python
from rest_framework.exceptions import Throttled

def drf_throttle(request, token=None):
    if should_throttle(token):
        raise Throttled()
```

### Audit sink

```python
KEYSMITH = {"AUDIT_LOG_HOOK": "myapp.hooks.audit"}
```

```python
def audit(*, action, token, request, status_code, extra, payload):
    """Replaces default DB write entirely."""
    publish(action, payload)
```

`payload` contains: `path`, `method`, `status_code`, `ip_address`, `user_agent`.

---

## Error messages

Override user-facing strings without changing code:

```python
KEYSMITH = {
    "DEFAULT_ERROR_MESSAGES": {
        "invalid_token": "Invalid API key.",
        "insufficient_scope": "Insufficient permissions.",
    },
}
```

Unspecified keys keep their built-in defaults (lazy-translated).

---

## Settings proxy

```python
from keysmith.settings import keysmith_settings

keysmith_settings.HASH_ITERATIONS
keysmith_settings.reload()  # clear cached values (tests)
```

---

**See also:** [Settings](../topics/settings.md) · [Security](security.md)
