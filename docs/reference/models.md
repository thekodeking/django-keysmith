# Models

## `Token`

**Module:** `keysmith.models.Token`  
**Table:** `keysmith_token`  
**Base:** `keysmith.models.base.AbstractToken`

### Fields

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `UUIDField` | Primary key |
| `name` | `CharField(128)` | Required |
| `description` | `TextField` | Optional |
| `created_by` | FK → User | `SET_NULL`, nullable |
| `user` | FK → User | `CASCADE`, nullable - request identity |
| `token_type` | `CharField` | `"user"` or `"system"` |
| `scopes` | M2M → Permission | Authorization codenames |
| `key` | `CharField(256)` | Hashed secret, unique |
| `prefix` | `CharField(255)` | Lookup key, unique |
| `created_at` | `DateTimeField` | Auto-set |
| `expires_at` | `DateTimeField` | Nullable |
| `last_used_at` | `DateTimeField` | Updated on auth |
| `revoked` | `BooleanField` | Default `False` |
| `purged` | `BooleanField` | Default `False` |

### Methods

| Method | Returns | Description |
| --- | --- | --- |
| `is_expired` | `bool` | Property |
| `is_active` | `bool` | Property - not revoked, purged, or expired |
| `can_authenticate()` | `bool` | Required on custom models |
| `mark_used(commit=True)` | `None` | Update `last_used_at` |

### Indexes

`key`, `expires_at`, `revoked`

---

## `TokenAuditLog`

**Module:** `keysmith.models.TokenAuditLog`  
**Table:** `keysmith_token_audit_log`  
**Base:** `keysmith.models.base.AbstractTokenAuditLog`

### Fields

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `BigAutoField` | Primary key |
| `token` | FK → Token | `SET_NULL`, nullable |
| `action` | `CharField(64)` | See constants below |
| `path` | `TextField` | Request path |
| `method` | `CharField(10)` | HTTP method |
| `status_code` | `PositiveSmallIntegerField` | |
| `ip_address` | `GenericIPAddressField` | Nullable |
| `user_agent` | `TextField` | Nullable |
| `extra` | `JSONField` | Metadata |
| `created_at` | `DateTimeField` | Auto-set |

### Action constants

```python
ACTION_AUTH_SUCCESS = "auth_success"
ACTION_AUTH_FAILED  = "auth_failed"
ACTION_CREATED      = "created"
ACTION_REVOKED      = "revoked"
ACTION_ROTATED      = "rotated"
```

### Indexes

`token`, `action`, `created_at`, `ip_address`, `status_code`, `(action, created_at)`

---

## Model accessors

```python
from keysmith.models.utils import get_token_model, get_audit_log_model

Token = get_token_model()
AuditLog = get_audit_log_model()
```

---

## Swappable models {#swappable-models}

```python
KEYSMITH = {
    "TOKEN_MODEL": "myapp.MyToken",
    "AUDIT_LOG_MODEL": "myapp.MyAuditLog",
}
```

Subclass the abstract bases for the easiest path:

```python
from keysmith.models.base import AbstractToken, AbstractTokenAuditLog

class MyToken(AbstractToken):
    class Meta(AbstractToken.Meta):
        db_table = "my_token"
```

### Required token fields

`key`, `prefix`, `revoked`, `purged`, `expires_at`, `last_used_at`, `user`

### Required token methods

`can_authenticate()`

### Required audit fields

`token`, `action`, `path`, `method`, `status_code`, `ip_address`, `user_agent`, `extra`, `created_at`

Validated by system checks `keysmith.E001`–`E003` at startup.
