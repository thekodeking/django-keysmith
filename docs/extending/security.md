# Production Security Checklist

A security hardening guide for running `django-keysmith` in production environments.

---

## 1. Always Enforce HTTPS

API tokens transmitted over plaintext HTTP can be intercepted by intermediate proxies or network eavesdroppers.

Ensure HTTPS is strictly enforced in your production `settings.py`:

```python
# settings.py (Production)

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 2. Choosing the Right Hasher for Your Threat Model

Keysmith hashes token secrets using one-way cryptographic functions.

| Hasher Backend | Brute-Force Cost | CPU Latency | Best Used In |
| :--- | :--- | :--- | :--- |
| **`PBKDF2SHA512TokenHasher`** | **Very High** (100k rounds) | ~10–25ms per check | Public APIs, partner integrations where database breaches are the primary threat. |
| **`HMACSHA256TokenHasher`** | **Impossible without `SECRET_KEY`** | < 0.1ms | Private microservices, high-traffic internal APIs. |
| **`SHA256TokenHasher`** | Low if database leaked | < 0.05ms | High-throughput APIs where tokens have high entropy (32+ chars) and low lifetime. |

!!! tip "Performance Balance"
    If your API handles thousands of requests per second, `PBKDF2` may consume significant CPU resources. Consider `HMACSHA256TokenHasher`, which runs in sub-millisecond time while remaining mathematically unforgeable without your application's `SECRET_KEY`.

---

## 3. Defense Against Timing Attacks

Keysmith exclusively uses Django's `constant_time_compare()` when comparing token hashes.

A standard string equality comparison (`==`) terminates at the first differing byte, allowing an attacker to determine the hash character-by-character by measuring response timing variations down to nanoseconds. Constant-time comparisons guarantee that verification always takes the exact same duration regardless of matching prefix length.

---

## 4. Reverse Proxy & Header Spoofing

Never enable `TRUST_PROXIES = True` unless your Django application sits directly behind a trusted reverse proxy (Nginx, Caddy, AWS ALB, Cloudflare) that actively strips or overwrites untrusted incoming `X-Forwarded-For` headers.

If an attacker sends a spoofed `X-Forwarded-For: 127.0.0.1` header directly to your application without proxy sanitation, an untrusted proxy configuration could falsify your audit trail.

---

## 5. Secret Entropy & Length

Keysmith enforces a minimum token secret length of 16 characters (default: 32 characters) via Django system checks (`keysmith.E007`):

```python
# settings.py

KEYSMITH = {
    # 32 characters of cryptographically secure random alphanumeric characters
    # provides ~190 bits of entropy, well beyond brute-force feasibility.
    "TOKEN_SECRET_LENGTH": 32,
}
```

---

## 6. Audit Trail Compliance & Privacy (GDPR / CCPA)

Audit logs store IP addresses and request paths. Depending on your jurisdiction:

1. **Retention Windows**: Do not retain audit logs indefinitely. Configure `python manage.py prune_audit_logs --days 90` to automatically delete records after your compliance window closes.
2. **IP Masking**: If required by privacy regulations, use `CLIENT_IP_HOOK` to truncate or anonymize the last octet of IPv4 addresses before saving.
