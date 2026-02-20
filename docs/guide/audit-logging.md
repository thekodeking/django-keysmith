# Audit Logging

Keysmith logs both authentication attempts and token lifecycle events. This gives you a traceable record for incident response, compliance reviews, and debugging failed access.

## Logged Actions

These action values are part of the model contract and can be used for dashboards and alerts.

- `auth_success`
- `auth_failed`
- `revoked`
- `rotated`

## Stored Context

Audit rows are request-aware when a request object is available, and still valid when events are written from non-request code paths.

Each audit row may include:

- `token` (nullable)
- `path`, `method`, `status_code`
- `ip_address`, `user_agent`
- `extra` JSON metadata

## Query Patterns

Use these query shapes as a starting point for admin pages or background analytics jobs.

```python
from keysmith.models import TokenAuditLog

failed = TokenAuditLog.objects.filter(
    action=TokenAuditLog.ACTION_AUTH_FAILED,
).order_by("-created_at")[:50]

recent_token_activity = TokenAuditLog.objects.filter(
    token=token,
).order_by("-created_at")[:100]
```

## Manual Events

You can write custom audit rows for related business events when you want one consolidated audit stream.

```python
from keysmith.audit.logger import log_audit_event

log_audit_event(
    action="auth_failed",
    request=request,
    token=token,
    status_code=401,
    extra={"error_code": "invalid_token", "actor_id": request.user.pk},
)
```

## Disable Logging

Disable audit logging only when you intentionally accept lower visibility.

```python
KEYSMITH = {
    "ENABLE_AUDIT_LOGGING": False,
}
```

## Retention Example

Retention policies should match your compliance and operational needs.

```python
from datetime import timedelta
from django.utils import timezone
from keysmith.models import TokenAuditLog

cutoff = timezone.now() - timedelta(days=90)
TokenAuditLog.objects.filter(created_at__lt=cutoff).delete()
```

Keysmith intentionally swallows audit write failures so authentication remains available.
