# Audit Logging & Client IP Tracking

Keysmith includes an immutable audit log system that tracks every authentication attempt and token lifecycle event.

---

## What Gets Logged?

Every audit record in the `keysmith_token_audit_log` table captures:

| Field | Description | Example |
| :--- | :--- | :--- |
| `token` | Foreign key to the token instance (set to `NULL` if token is deleted) | `tok_a1B2c3D4` |
| `action` | The event action type | `authenticated`, `auth_failed`, `created`, `rotated`, `revoked`, `purged` |
| `path` & `method` | The request URL path and HTTP verb | `POST /api/v1/orders/` |
| `status_code` | The resulting HTTP response code | `200`, `401`, `403` |
| `ip_address` | The client IP address (validated IPv4/IPv6) | `198.51.100.42` |
| `user_agent` | The client HTTP User-Agent string | `curl/8.1.2`, `python-httpx/0.27.0` |
| `actor` | The user who triggered the action (if created/rotated via admin/service) | `admin_user` |
| `extra` | JSON dictionary containing error details or context metadata | `{"error": "ExpiredToken"}` |
| `created_at` | Timestamp of the event in UTC | `2026-09-03 14:20:00` |

---

## Client IP Resolution & Proxy Trust

Accurate client IP tracking is vital for security auditing, anomaly detection, and rate limiting.

Keysmith resolves the client IP using a secure 4-stage priority order:

```text
1. Custom Hook (CLIENT_IP_HOOK)
   └── Executes custom callable or dotted function.
       │
       ▼
2. Custom Header (CLIENT_IP_HEADER)
   └── e.g. "HTTP_X_REAL_IP" or "HTTP_CF_CONNECTING_IP"
       │
       ▼
3. Reverse Proxy Forward (HTTP_X_FORWARDED_FOR)
   └── Used ONLY if TRUST_PROXIES = True
       │
       ▼
4. Socket Remote Address (REMOTE_ADDR)
   └── Direct TCP connection IP
```

### Cloudflare or Custom Reverse Proxies

If you are behind Cloudflare, AWS ALB, Nginx, or Fly.io, configure the header your proxy sends:

```python
# settings.py

KEYSMITH = {
    # If behind Cloudflare:
    "CLIENT_IP_HEADER": "HTTP_CF_CONNECTING_IP",

    # Or if behind an internal trusted proxy using X-Forwarded-For:
    "TRUST_PROXIES": True,
}
```

### Using a Custom Client IP Hook

For complex multi-tier infrastructures, define a custom IP resolution function:

```python
# myproject/utils.py

def resolve_secure_ip(request):
    # Custom logic to inspect headers or validate VPC CIDRs
    return request.META.get("HTTP_TRUE_CLIENT_IP") or request.META.get("REMOTE_ADDR")
```

Register it in your settings:

```python
# settings.py

KEYSMITH = {
    "CLIENT_IP_HOOK": "myproject.utils.resolve_secure_ip",
    # Or pass the callable directly:
    # "CLIENT_IP_HOOK": resolve_secure_ip,
}
```

!!! tip "IP Validation"
    Keysmith automatically validates that the extracted value is a valid IPv4 or IPv6 string using Python's `ipaddress` module, preventing header injection attacks into your database.

---

## Custom Audit Hook (`AUDIT_LOG_HOOK`)

Want to stream audit events to Datadog, AWS CloudWatch, Sentry, or an external SIEM? Register an `AUDIT_LOG_HOOK`:

```python
# myproject/audit.py

def stream_to_datadog(event_data):
    """
    event_data is a dictionary containing:
    action, token, path, method, status_code, ip_address, extra, etc.
    """
    statsd.increment(
        "api.token.access",
        tags=[f"action:{event_data['action']}", f"status:{event_data['status_code']}"]
    )
```

```python
# settings.py

KEYSMITH = {
    "AUDIT_LOG_HOOK": "myproject.audit.stream_to_datadog",
}
```

---

## Log Retention & Pruning

Audit tables grow rapidly in high-traffic APIs. Keysmith includes a retention pruning management command:

```bash
# Delete all audit log entries older than 90 days:
python manage.py prune_audit_logs --days 90
```

### Automated Retention via Cron or Celery

Schedule `prune_audit_logs` to run daily in your crontab or task scheduler:

```cron
# Run daily at 3:00 AM UTC
0 3 * * * /path/to/venv/bin/python /path/to/project/manage.py prune_audit_logs --days 90
```
