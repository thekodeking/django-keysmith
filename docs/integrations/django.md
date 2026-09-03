# Standard Django Integration

Use middleware, decorators, and mixins when building APIs with standard Django views (Function-Based or Class-Based) without Django REST Framework.

---

## 1. Setup Middleware

Add `KeysmithAuthenticationMiddleware` directly after Django's `AuthenticationMiddleware`:

```python
# settings.py

MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
]
```

### How the Middleware Operates

The middleware runs on every incoming request:

```text
Incoming HTTP Request
          │
          ▼
┌──────────────────────────────────────────────────────────┐
│ KeysmithAuthenticationMiddleware                         │
│ 1. Extracts token from Authorization header or custom    │
│    X-KEYSMITH-TOKEN header.                              │
│ 2. Validates CRC32 checksum & verifies database state.   │
│ 3. Attaches results to request:                          │
│    - request.keysmith_token = Token instance (or None)   │
│    - request.keysmith_user  = Linked user (or None)      │
│    - request.keysmith_auth_error = Exception (or None)   │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼ (Never blocks public requests!)
                      Target View
```

!!! tip "Non-Blocking Architecture"
    The middleware **never blocks or rejects unauthenticated requests on its own**. Public endpoints, admin views, and web pages proceed normally. Views explicitly enforce authentication using the `@keysmith_required` decorator or mixin.

---

## 2. Protecting Function-Based Views (FBVs)

Use the `@keysmith_required` decorator to enforce token authentication:

```python
# views.py
from django.http import JsonResponse
from keysmith.django.decorator import keysmith_required, require_scopes

@keysmith_required
def status_api(request):
    return JsonResponse({
        "status": "online",
        "token_prefix": request.keysmith_token.prefix,
        "username": getattr(request.keysmith_user, "username", None),
    })
```

### Enforcing Scopes

Stack `@require_scopes` to ensure the token possesses specific permissions:

```python
@keysmith_required
@require_scopes("billing.view_invoice", "billing.create_charge")
def process_charge(request):
    # Only tokens with both billing scopes can execute this view
    return JsonResponse({"status": "charge processed"})
```

If the token lacks any required scope, Keysmith returns `403 Forbidden`:

```json
{"detail": "Token does not have required scope: billing.create_charge"}
```

---

## 3. Protecting Class-Based Views (CBVs)

For Django Class-Based Views, inherit from `KeysmithRequiredMixin`:

```python
# views.py
from django.views import View
from django.http import JsonResponse
from keysmith.django.mixins import KeysmithRequiredMixin

class CustomerProfileView(KeysmithRequiredMixin, View):
    required_scopes = ["customers.view_customer"]

    def get(self, request, *args, **kwargs):
        token = request.keysmith_token
        return JsonResponse({
            "token": token.prefix,
            "user": request.keysmith_user.username,
        })
```

---

## 4. Accessing Request Context

When a request is authenticated, Keysmith provides several context attributes on the `request` object:

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `request.keysmith_token` | `Token | None` | The active `Token` database instance. |
| `request.keysmith_user` | `User | None` | The Django `User` linked to the token (or `None` for system tokens). |
| `request.keysmith_auth_error` | `Exception | None` | If authentication failed, contains the exception (e.g. `InvalidToken`, `ExpiredToken`, `RevokedToken`). |

---

## 5. Customizing Unauthorized Responses

By default, `@keysmith_required` returns a JSON response:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api"
Content-Type: application/json

{
  "detail": "Invalid token format or token does not exist."
}
```

If you need a custom JSON schema or error payload, inspect `request.keysmith_auth_error` in a custom decorator or exception handler.
