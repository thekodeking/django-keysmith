# Tutorial

This tutorial takes you from zero to a working authenticated endpoint. It assumes you completed [Install](install.md).

---

## Step 1 - Create a token

Tokens can exist without a linked user, but attaching one populates `request.user` / `request.keysmith_user` in your views.

```python
from django.contrib.auth import get_user_model
from keysmith.services.tokens import create_token

user = get_user_model().objects.get(username="api-user")

token, raw_token = create_token(
    name="tutorial-token",
    user=user,
)

print(raw_token)   # copy this somewhere safe
print(token.prefix)
```

!!! tip
    You can also create tokens from the [Django admin](../topics/admin.md). The raw secret is shown once after creation.

---

## Step 2 - Protect an endpoint

=== "Django"

    ```python
    # views.py
    from django.http import JsonResponse
    from keysmith.django.decorator import keysmith_required

    @keysmith_required
    def status(request):
        return JsonResponse({
            "ok": True,
            "prefix": request.keysmith_token.prefix,
        })
    ```

    ```python
    # urls.py
    from django.urls import path
    from . import views

    urlpatterns = [
        path("api/status/", views.status),
    ]
    ```

=== "DRF"

    ```python
    # views.py
    from rest_framework.response import Response
    from rest_framework.views import APIView
    from keysmith.drf.permissions import RequireKeysmithToken

    class StatusView(APIView):
        permission_classes = [RequireKeysmithToken]

        def get(self, request):
            return Response({
                "ok": True,
                "prefix": request.auth.prefix,
            })
    ```

    If you set [global DRF defaults](install.md#optional-drf-defaults), you can omit `permission_classes`.

---

## Step 3 - Make a request

Send the raw token in the `X-KEYSMITH-TOKEN` header:

```bash
curl -s -H "X-KEYSMITH-TOKEN: <raw-token>" \
  http://localhost:8000/api/status/
```

Expected response:

```json
{"ok": true, "prefix": "tok_..."}
```

Without a token (or with an invalid one), protected endpoints return `401 Unauthorized`.

---

## Step 4 - Rotate the token

If a secret is exposed, rotate immediately. The old raw token stops working at once; the database record (prefix, scopes, metadata) is preserved.

```python
from keysmith.services.tokens import rotate_token

new_raw_token = rotate_token(token, actor=user, request=request)
```

Hand `new_raw_token` to the client. The previous value is now invalid.

---

## Step 5 - Revoke the token

When a credential is permanently retired:

```python
from keysmith.services.tokens import revoke_token

revoke_token(token, actor=user, request=request)
```

The token can no longer authenticate. A `revoked` audit event is recorded.

---

## What you learned

| Concept | Detail |
| --- | --- |
| Raw token | Shown once at creation; never stored in plaintext |
| Header | `X-KEYSMITH-TOKEN` by default |
| Django | `@keysmith_required` + middleware |
| DRF | `KeysmithAuthentication` + `RequireKeysmithToken` |
| Lifecycle | `rotate_token` and `revoke_token` via service API |

---

## Continue reading

- [Tokens](../topics/tokens.md) - expiry, purge, queries, lifecycle states
- [Scopes](../topics/scopes.md) - restrict what a token can do
- [Settings](../topics/settings.md) - configure expiry, headers, and more
