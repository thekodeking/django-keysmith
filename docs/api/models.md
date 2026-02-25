# Models API

This page describes the default concrete models shipped with Keysmith and the compatibility requirements when swapping them out.

## `Token`

Concrete model: `keysmith.models.Token`.

The token model stores lifecycle state and metadata while keeping the secret itself hashed.

Key fields:

- `id` (UUID primary key)
- `name`, `description`
- `created_by`, `user`
- `token_type` (`user` or `system`)
- `scopes` (`ManyToMany` to `auth.Permission`)
- `key` (hashed secret)
- `prefix`
- `created_at`, `expires_at`, `last_used_at`
- `revoked`, `purged`

Key helpers:

- `is_expired`
- `is_active`
- `can_authenticate()`
- `mark_used(commit=True)`

## `TokenAuditLog`

Concrete model: `keysmith.models.TokenAuditLog`.

Audit rows capture request metadata and lifecycle operations for observability and investigation.

Key fields:

- `token`
- `action`
- `path`, `method`, `status_code`
- `ip_address`, `user_agent`
- `extra` (JSON)
- `created_at`

Action constants:

- `TokenAuditLog.ACTION_AUTH_SUCCESS`
- `TokenAuditLog.ACTION_AUTH_FAILED`
- `TokenAuditLog.ACTION_REVOKED`
- `TokenAuditLog.ACTION_ROTATED`

## Custom Model Configuration

If you need custom tables or additional fields, point settings to your model classes.

```python
KEYSMITH = {
    "TOKEN_MODEL": "myapp.MyToken",
    "AUDIT_LOG_MODEL": "myapp.MyAuditLog",
}
```

Configured models are validated by Django system checks at startup.

Required token fields include:

- `key`, `prefix`, `revoked`, `purged`, `expires_at`, `last_used_at`, `user`

Required audit fields include:

- `token`, `action`, `path`, `method`, `status_code`, `ip_address`, `user_agent`, `extra`, `created_at`
