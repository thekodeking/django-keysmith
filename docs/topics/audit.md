# Audit logs

Keysmith writes an audit row for authentication attempts and token lifecycle changes. Use these records for incident response, compliance, and debugging access failures.

---

## Logged actions

| Action | Trigger |
| --- | --- |
| `auth_success` | Token validated successfully |
| `auth_failed` | Validation failed on a protected endpoint |
| `created` | `create_token()` |
| `rotated` | `rotate_token()` |
| `revoked` | `revoke_token()` or `purge_token()` |

---

## What each row stores

| Field | Content |
| --- | --- |
| `token` | Related token (nullable for some failures) |
| `action` | One of the actions above |
| `path`, `method` | Request path and HTTP verb |
| `status_code` | HTTP response status |
| `ip_address` | Client IP (`REMOTE_ADDR` or `X-Forwarded-For` when `TRUST_PROXIES=True`) |
| `user_agent` | Client user agent |
| `extra` | JSON metadata - actor ID, error codes, purge flag, etc. |
| `created_at` | Timestamp |

The `extra` field on `auth_failed` events includes an `error_code` such as `missing_token`, `invalidtoken`, `revokedtoken`, or `expiredtoken`.

---

## Querying

```python
from keysmith.models import TokenAuditLog

# Recent failures
TokenAuditLog.objects.filter(
    action=TokenAuditLog.ACTION_AUTH_FAILED,
).order_by("-created_at")[:50]

# Activity for one token
TokenAuditLog.objects.filter(token=token).order_by("-created_at")
```

Action constants are defined on the model:

```python
TokenAuditLog.ACTION_AUTH_SUCCESS   # "auth_success"
TokenAuditLog.ACTION_AUTH_FAILED    # "auth_failed"
TokenAuditLog.ACTION_CREATED        # "created"
TokenAuditLog.ACTION_REVOKED        # "revoked"
TokenAuditLog.ACTION_ROTATED        # "rotated"
```

---

## Custom events

Write to the same stream from application code:

```python
from keysmith.audit.logger import log_audit_event

log_audit_event(
    action="auth_failed",
    request=request,
    token=token,
    status_code=401,
    extra={"error_code": "custom_reason"},
)
```

No-op when `ENABLE_AUDIT_LOGGING=False`.

---

## Custom sink

Send events to an external system instead of the database:

```python
KEYSMITH = {
    "AUDIT_LOG_HOOK": "myapp.logging.audit_sink",
}
```

```python
def audit_sink(*, action, token, request, status_code, extra, payload):
    send_to_datadog(action, payload)
```

When a hook is configured, it **replaces** the default database write entirely.

---

## Retention

Prune old rows with the management command:

```bash
python manage.py prune_audit_logs --days 90
```

If `--days` is omitted, `AUDIT_LOG_RETENTION_DAYS` from settings is used. Without either, the command prints a warning and exits without deleting anything.

---

## Failure behavior

Audit write failures are always swallowed - authentication is never blocked by a logging outage. If audit integrity is critical, use `AUDIT_LOG_HOOK` to send events to a durable external system.

---

**See also:** [Settings - audit](settings.md#audit-logging) · [Commands reference](../reference/commands.md)
