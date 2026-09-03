# Configuration & Settings

All configuration options are defined in your Django `settings.py` under the `KEYSMITH` dictionary.

```python
# settings.py

KEYSMITH = {
    "HASH_BACKEND": "keysmith.hashers.PBKDF2SHA512TokenHasher",
    "DEFAULT_EXPIRY_DAYS": 90,
    "HEADER_NAME": "HTTP_X_KEYSMITH_TOKEN",
    "LAST_USED_UPDATE_INTERVAL": 60,
}
```

---

## 1. Token Hashing & Cryptography

| Setting | Type | Default | Description |
| :--- | :---: | :--- | :--- |
| `HASH_BACKEND` | `str` | `"keysmith.hashers.PBKDF2SHA512TokenHasher"` | Dotted path to the hasher class. Built-in options: `PBKDF2SHA512TokenHasher`, `SHA256TokenHasher`, `HMACSHA256TokenHasher`. |
| `HASH_ITERATIONS` | `int` | `100_000` | Number of PBKDF2 stretching rounds (minimum 10,000 enforced by system checks). Only used when `HASH_BACKEND` is PBKDF2. |
| `TOKEN_PREFIX` | `str` | `"tok"` | Leading prefix for generated tokens (e.g. `tok_...`). Max 16 characters. |
| `TOKEN_SECRET_LENGTH` | `int` | `32` | Character length of the random secret (minimum 16 enforced by system checks). |

---

## 2. Authentication & Headers

| Setting | Type | Default | Description |
| :--- | :---: | :--- | :--- |
| `AUTH_HEADER_TYPES` | `tuple` | `("Bearer", "Token")` | Accepted prefixes in the HTTP `Authorization` header. |
| `WWW_AUTHENTICATE_SCHEME` | `str` | `"Bearer"` | Challenge scheme emitted in `WWW-Authenticate` on 401 Unauthorized per RFC 9110. |
| `HEADER_NAME` | `str` | `"HTTP_X_KEYSMITH_TOKEN"` | Alternative custom header name in Django's `request.META` format (`HTTP_<HEADER>`). |
| `ALLOW_QUERY_PARAM` | `bool` | `False` | Whether to accept tokens via URL query string (useful for constrained webhooks). |
| `QUERY_PARAM_NAME` | `str` | `"keysmith_token"` | Name of the query parameter when `ALLOW_QUERY_PARAM = True`. |

---

## 3. Performance & Usage Tracking

| Setting | Type | Default | Description |
| :--- | :---: | :--- | :--- |
| `LAST_USED_UPDATE_INTERVAL` | `int` | `60` | Minimum seconds between database writes to `last_used_at`. Set to `0` to update on every single request. |
| `DEFAULT_EXPIRY_DAYS` | `int` | `90` | Number of days before newly created tokens expire if no custom `expires_at` is provided. |

---

## 4. Client IP & Proxies

| Setting | Type | Default | Description |
| :--- | :---: | :--- | :--- |
| `CLIENT_IP_HEADER` | `str | None` | `None` | Custom header for client IP (e.g. `"HTTP_CF_CONNECTING_IP"`, `"HTTP_X_REAL_IP"`). |
| `CLIENT_IP_HOOK` | `callable | str` | `None` | Custom callable or dotted path `hook(request) -> str` to resolve client IP. |
| `TRUST_PROXIES` | `bool` | `False` | When `True`, reads client IP from `HTTP_X_FORWARDED_FOR`. Only enable behind trusted reverse proxies. |

---

## 5. Scopes & Model Customization

| Setting | Type | Default | Description |
| :--- | :---: | :--- | :--- |
| `AVAILABLE_SCOPES` | `list[str]` | `[]` | List of Django permission strings (`"<app_label>.<codename>"`) allowed for tokens. |
| `DEFAULT_SCOPES` | `list[str]` | `[]` | Scopes automatically assigned to newly issued tokens if none are specified. |
| `TOKEN_MODEL` | `str` | `"keysmith.Token"` | Swappable model path if extending the base token model with custom fields. |

---

## 6. Custom Callables & Hooks

All hooks accept either a dotted import string (e.g. `"myapp.hooks.my_hook"`) or a **direct Python callable**:

| Hook | Signature | Description |
| :--- | :--- | :--- |
| `AUDIT_LOG_HOOK` | `hook(event_data: dict) -> None` | Invoked after every audit event is generated. Perfect for Datadog, Sentry, or SIEM pipelines. |
| `RATE_LIMIT_HOOK` | `hook(request, raw_token=None) -> None` | Custom rate limit checker for Django middleware views. Raise an exception or return a response if throttled. |
| `DRF_THROTTLE_HOOK` | `hook(request, token=None) -> None` | Custom throttle hook invoked inside `KeysmithAuthentication`. |
| `CLIENT_IP_HOOK` | `hook(request) -> str | None` | Resolves the client IP address from the request object. |

---

## 7. Custom Error Messages

Customize human-facing error messages returned on authentication failures:

```python
# settings.py

KEYSMITH = {
    "DEFAULT_ERROR_MESSAGES": {
        "invalid_token": "The API key provided is malformed or invalid.",
        "expired_token": "This API key has expired. Please regenerate your key in settings.",
        "revoked_token": "This API key has been deactivated by an administrator.",
    }
}
```
