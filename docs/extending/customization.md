# Customization & Extensibility

Customize models, hash algorithms, client IP resolution, and external audit integrations.

---

## 1. Swapping the Token Model (`TOKEN_MODEL`)

If you need to add custom fields to tokens (e.g. `tenant_id`, `rate_limit_tier`, `allowed_cidrs`, or `billing_tier`), extend Keysmith's abstract models.

### Step 1: Subclass `AbstractToken`

```python
# myapp/models.py
from django.db import models
from keysmith.models import AbstractToken, AbstractTokenAuditLog

class OrganizationToken(AbstractToken):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="api_tokens",
    )
    is_internal = models.BooleanField(default=False)

    class Meta(AbstractToken.Meta):
        swappable = "KEYSMITH_TOKEN_MODEL"

class OrganizationTokenAuditLog(AbstractTokenAuditLog):
    class Meta(AbstractTokenAuditLog.Meta):
        swappable = "KEYSMITH_AUDIT_LOG_MODEL"
```

### Step 2: Register in `settings.py`

```python
# settings.py

KEYSMITH = {
    "TOKEN_MODEL": "myapp.OrganizationToken",
}
```

Keysmith's services, admin views, and authentication decorators automatically detect and use your custom model!

---

## 2. Token Hashing Backends

Keysmith provides three built-in token hashers tailored for different performance and security profiles:

### Built-In Hashers

| Hasher Backend | Algorithm | Cryptographic Profile | Recommended For |
| :--- | :--- | :--- | :--- |
| **`PBKDF2SHA512TokenHasher`** *(default)* | PBKDF2 with SHA-512 (100,000 iterations) | Compute-intensive, slow brute-force resistance. | Standard applications, partner integrations. |
| **`SHA256TokenHasher`** | Single-round SHA-256 | Ultra-fast (< 0.1ms), zero CPU overhead. | High-throughput APIs (> 5,000 req/sec) where PBKDF2 adds too much CPU latency. |
| **`HMACSHA256TokenHasher`** | HMAC-SHA256 keyed with Django's `SECRET_KEY` | Fast, keyed MAC. Impossible to verify or brute-force without the application secret. | Internal microservices, distributed cluster deployments. |

### Switching the Hasher

To switch to the fast HMAC-SHA256 hasher:

```python
# settings.py

KEYSMITH = {
    "HASH_BACKEND": "keysmith.hashers.HMACSHA256TokenHasher",
}
```

### Implementing a Custom Hasher

You can implement your own hashing logic (e.g. Argon2, BLAKE3) by subclassing `BaseTokenHasher`:

```python
# myapp/hashers.py
import hashlib
from keysmith.hashers.base import BaseTokenHasher

class Blake3TokenHasher(BaseTokenHasher):
    algorithm = "blake3"

    def hash(self, secret: str) -> str:
        # Return a formatted string: "blake3$<hash>"
        digest = hashlib.blake2s(secret.encode("utf-8")).hexdigest()
        return f"{self.algorithm}${digest}"

    def verify(self, secret: str, encoded: str) -> bool:
        algorithm, digest = encoded.split("$", 1)
        expected = hashlib.blake2s(secret.encode("utf-8")).hexdigest()
        return constant_time_compare(digest, expected)
```

Register it in `settings.py`:

```python
# settings.py

KEYSMITH = {
    "HASH_BACKEND": "myapp.hashers.Blake3TokenHasher",
}
```

---

## 3. Custom Hooks

All hooks in Keysmith support both dotted string paths (e.g. `"myapp.hooks.my_hook"`) and **direct Python callables**:

### Client IP Hook (`CLIENT_IP_HOOK`)

Extract client IP addresses from complex multi-proxy topologies or custom VPC headers:

```python
def resolve_client_ip(request) -> str | None:
    return request.META.get("HTTP_X_CUSTOM_CLIENT_IP")

KEYSMITH = {
    "CLIENT_IP_HOOK": resolve_client_ip,
}
```

### External Audit Stream Hook (`AUDIT_LOG_HOOK`)

Stream audit events directly into external observability platforms (Datadog, Grafana Loki, AWS SQS, or Elasticsearch):

```python
def send_to_siem(event_data: dict) -> None:
    logger.info(
        "API Token Event",
        extra={
            "action": event_data["action"],
            "token": event_data["token"],
            "ip": event_data["ip_address"],
            "status": event_data["status_code"],
        }
    )

KEYSMITH = {
    "AUDIT_LOG_HOOK": send_to_siem,
}
```
