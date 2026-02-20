# Plain Django Integration

This page covers Keysmith usage in non-DRF Django views. Middleware and decorators provide request-level auth context without custom parsing code in each view.

## Middleware

Middleware should be enabled so token extraction and audit behavior are centralized.

```python
MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
]
```

Middleware attaches:

- `request.keysmith_token`
- `request.keysmith_user`
- `request.keysmith_auth_error`

## Protect Views

Use `@keysmith_required` to enforce token presence and validity before view logic executes.

```python
from django.http import JsonResponse
from keysmith.django.decorator import keysmith_required


@keysmith_required
def secure_view(request):
    return JsonResponse({"ok": True, "prefix": request.keysmith_token.prefix})
```

## Decorator Options

Decorator options let you customize behavior for mixed public/private endpoints and response messages.

`keysmith_required()` supports:

- `allow_anonymous`: allows missing token while still rejecting invalid token
- `missing_message`: custom 401 message for missing token
- `invalid_message`: custom 401 message for invalid/expired/revoked token

## Scope Checks

Layer `@keysmith_scopes(...)` after `@keysmith_required` when a view needs specific capabilities.

```python
from keysmith.django.permissions import keysmith_scopes


@keysmith_required
@keysmith_scopes("write")
def create_view(request):
    return JsonResponse({"created": True})
```

## Header vs Query Parameter

Headers are recommended because query strings are commonly logged by proxies and upstream services.

Default header:

```text
X-KEYSMITH-TOKEN: <raw-token>
```

Optional query parameter fallback:

```python
KEYSMITH = {
    "ALLOW_QUERY_PARAM": True,
    "QUERY_PARAM_NAME": "keysmith_token",
}
```

Use query parameters only when headers are not feasible.
