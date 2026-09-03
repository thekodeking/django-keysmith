# Django REST Framework (DRF) Integration

Integrate Keysmith with Django REST Framework to support API key authentication, permission scopes, and token rate limiting.

---

## 1. Quick Setup

Configure Keysmith in your `REST_FRAMEWORK` settings:

```python
# settings.py

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "keysmith.drf.auth.KeysmithAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "keysmith.drf.permissions.RequireKeysmithToken",
    ],
}
```

---

## 2. How DRF Authentication Works

`KeysmithAuthentication` integrates into DRF's standard authentication cycle:

```text
Incoming API Request
          │
          ▼
┌──────────────────────────────────────────────────────────┐
│ KeysmithAuthentication.authenticate(request)             │
│ 1. Extracts token from Authorization header              │
│    (Bearer <token> or Token <token>)                     │
│ 2. Validates CRC32 checksum & checks database state      │
│ 3. Returns (user, token) tuple:                          │
│    - request.user = token.user (or AnonymousUser)        │
│    - request.auth = Token model instance                 │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ DRF Permission Classes Check                             │
│ - RequireKeysmithToken: Ensures request.auth is a Token  │
│ - HasTokenScope: Ensures token has required scopes       │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ DRF Throttling (KeysmithTokenRateThrottle)               │
│ Enforces rate limits per token prefix or client IP       │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
                      API View Logic
```

---

## 3. Protecting Views & ViewSets

### Using APIView

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from keysmith.drf.permissions import RequireKeysmithToken, HasTokenScope

class AnalyticsView(APIView):
    # Require a valid Keysmith token with the analytics view permission:
    permission_classes = [RequireKeysmithToken, HasTokenScope]
    required_scopes = ["reports.view_analytics"]

    def get(self, request):
        return Response({
            "token": request.auth.prefix,
            "user": str(request.user),
            "data": [10, 20, 30],
        })
```

### Using ModelViewSet

```python
# views.py
from rest_framework import viewsets
from keysmith.drf.permissions import RequireKeysmithToken, HasTokenScope
from .models import Invoice
from .serializers import InvoiceSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [RequireKeysmithToken, HasTokenScope]

    # Dynamically specify scopes per action:
    def get_required_scopes(self):
        if self.action in ["create", "update", "partial_update"]:
            return ["invoices.change_invoice"]
        if self.action == "destroy":
            return ["invoices.delete_invoice"]
        return ["invoices.view_invoice"]
```

---

## 4. Rate Limiting with `KeysmithTokenRateThrottle`

Keysmith provides a dedicated rate-limiting throttle class for DRF:

```python
# settings.py

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "keysmith.drf.throttling.KeysmithTokenRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # 1,000 requests per hour per API token prefix
        "keysmith": "1000/hour",
    },
}
```

### How Throttling Works
- If a request is authenticated with a token, the rate limit is tracked **per token prefix** (`keysmith_tok_a1B2c3D4`).
- If unauthenticated, it falls back to rate-limiting by the client's validated IP address.
- Multiple application servers sharing Redis or Memcached enforce the limit globally.

You can also apply throttling per view:

```python
from keysmith.drf.throttling import KeysmithTokenRateThrottle

class HighVolumeExportView(APIView):
    throttle_classes = [KeysmithTokenRateThrottle]
    throttle_scope = "keysmith"
```

---

## 5. RFC 9110 Challenge Headers

When a request lacks credentials or fails authentication, `KeysmithAuthentication` automatically emits standard `WWW-Authenticate` headers:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api"
Content-Type: application/json

{
  "detail": "Authentication credentials were not provided."
}
```

You can customize the challenge scheme (e.g. `"Token"` instead of `"Bearer"`) via `WWW_AUTHENTICATE_SCHEME` in `settings.py`.
