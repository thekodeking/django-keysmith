# Permissions API Reference

Reference for Django decorators, DRF permission classes, and rate throttles.

---

## Django Permissions

Module: `keysmith.django.permissions` and `keysmith.django.decorator`

### `keysmith_required`

```python
from keysmith.django.decorator import keysmith_required

@keysmith_required
def view_func(request):
    ...
```

Ensures the incoming request possesses an active, valid Keysmith token.

#### Optional Parameters
- `allow_anonymous: bool = False`: If `True`, allows unauthenticated traffic through to the view. `request.keysmith_token` will be `None` if unauthenticated.
- `missing_message: str | None`: Custom error message if the token header is missing.
- `invalid_message: str | None`: Custom error message if the token is invalid or expired.

---

### `keysmith_scopes`

```python
from keysmith.django.permissions import keysmith_scopes

@keysmith_required
@keysmith_scopes("orders.view_order", "orders.add_order")
def view_func(request):
    ...
```

Verifies that the authenticated token has **all** specified scope codenames.

- If unauthenticated: Returns `401 Unauthorized`.
- If authenticated but missing any required scope: Raises `PermissionDenied` (HTTP `403 Forbidden`).

---

## DRF Permissions & Throttling

Module: `keysmith.drf.permissions` and `keysmith.drf.throttling`

### `RequireKeysmithToken`

```python
from keysmith.drf.permissions import RequireKeysmithToken

class MyAPIView(APIView):
    permission_classes = [RequireKeysmithToken]
```

Enforces that `request.auth` is an active `Token` database instance. If missing, raises DRF `NotAuthenticated` (HTTP 401).

---

### `HasKeysmithScopes`

```python
from keysmith.drf.permissions import HasKeysmithScopes

class MyAPIView(APIView):
    permission_classes = [RequireKeysmithToken, HasKeysmithScopes]
    required_scopes = {"orders.view_order"}
```

Validates token scopes against the view's `required_scopes` attribute.

---

### `ScopedPermission`

Helper function to dynamically generate a DRF permission class requiring specific scopes:

```python
from keysmith.drf.permissions import ScopedPermission

class MyAPIView(APIView):
    permission_classes = [ScopedPermission("orders.view_order", "orders.add_order")]
```

---

### `KeysmithTokenRateThrottle`

```python
from keysmith.drf.throttling import KeysmithTokenRateThrottle

class HighThroughputView(APIView):
    throttle_classes = [KeysmithTokenRateThrottle]
    throttle_scope = "keysmith"
```

Tracks and enforces rate limits per token prefix (`keysmith_<prefix>`). If the request is unauthenticated, it falls back to the client's validated IP address.
