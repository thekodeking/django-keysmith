# Django REST Framework Integration

This page shows how to use Keysmith as a first-class DRF authentication and authorization layer. The focus is keeping your views simple while centralizing token behavior.

## Install

Install the DRF extra when your project uses DRF views or viewsets.

```bash
pip install "django-keysmith[drf]"
```

## Configure DRF

Set global DRF defaults so token auth is applied consistently across endpoints.

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "keysmith.drf.auth.KeysmithAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "keysmith.drf.permissions.RequireKeysmithToken",
    ],
}
```

## Basic Protected Endpoint

Once defaults are in place, views can focus on business behavior and safely rely on `request.auth`.

```python
from rest_framework.response import Response
from rest_framework.views import APIView


class StatusView(APIView):
    def get(self, request):
        return Response(
            {
                "authenticated": True,
                "token_prefix": request.auth.prefix,
                "user_id": getattr(request.user, "pk", None),
            }
        )
```

## Scope-Protected Endpoint

Add scope checks when endpoints need finer-grained permissions than authentication alone.

```python
from keysmith.drf.permissions import RequireKeysmithToken, ScopedPermission


class WriteView(APIView):
    permission_classes = [RequireKeysmithToken, ScopedPermission("write")]

    def post(self, request):
        ...
```

## Header Configuration

By default, clients send tokens in `X-KEYSMITH-TOKEN`. This maps from Django META header naming conventions.

Default client header:

```text
X-KEYSMITH-TOKEN: <raw-token>
```

Mapped from `KEYSMITH["HEADER_NAME"] = "HTTP_X_KEYSMITH_TOKEN"`.

## Optional Throttle Hook

Use `DRF_THROTTLE_HOOK` when throttling needs token-aware logic that runs after successful authentication.

```python
from rest_framework.exceptions import Throttled

KEYSMITH = {
    "DRF_THROTTLE_HOOK": "myapp.auth.throttle_hook",
}


def throttle_hook(request, token=None):
    if should_throttle(token):
        raise Throttled(detail="Too many requests")
```

## Test Example

A minimal test should verify successful auth and expected response code using the same header clients will send.

```python
client.credentials(HTTP_X_KEYSMITH_TOKEN=raw_token)
response = client.get("/api/drf/status/")
assert response.status_code == 200
```
