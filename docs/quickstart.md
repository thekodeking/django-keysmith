# Quick Start

This walkthrough creates a token and uses it against a protected DRF endpoint. It is meant to give you a fast end-to-end check before deeper configuration work.

## 1. Create a Token

Start by creating a token linked to a user so request identity is populated in authenticated views.

```python
from django.contrib.auth import get_user_model
from keysmith.services.tokens import create_token

User = get_user_model()
user = User.objects.get(username="api-user")

token, raw_token = create_token(
    name="local-dev",
    user=user,
)

print("Prefix:", token.prefix)
print("Raw token:", raw_token)
```

The returned raw token is shown once. The database stores only a hash.

## 2. Protect an Endpoint

Apply `RequireKeysmithToken` on DRF views to enforce token authentication before request handling.

```python
from rest_framework.response import Response
from rest_framework.views import APIView
from keysmith.drf.permissions import RequireKeysmithToken


class HealthView(APIView):
    permission_classes = [RequireKeysmithToken]

    def get(self, request):
        return Response(
            {
                "ok": True,
                "token_prefix": request.auth.prefix,
            }
        )
```

## 3. Call the Endpoint

Use the raw token in `X-KEYSMITH-TOKEN` and confirm the endpoint responds with `200`.

```bash
curl -H "X-KEYSMITH-TOKEN: <raw-token>" \
  http://localhost:8000/api/health/
```

## 4. Rotate or Revoke

Lifecycle actions should be part of your normal operations. Rotation invalidates previous raw tokens immediately.

```python
from keysmith.services.tokens import purge_token, revoke_token, rotate_token

new_raw_token = rotate_token(token)
# old token is now invalid

revoke_token(token)
# token is permanently invalid

purge_token(token)
# token is soft-deleted (purged + revoked)
```

## Notes for Plain Django Views

If you protect plain Django views with `@keysmith_required`, create tokens with a linked user (`user=...`) so `request.keysmith_user` is available for your view code and audit context.

Next:

- [Configuration](configuration.md)
- [Token Management](guide/token-management.md)
