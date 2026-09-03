# Tutorial

This tutorial guides you step-by-step through creating tokens, securing endpoints, inspecting audit logs, and rotating credentials.

---

## The Scenario

Imagine you are building an API endpoint for an external partner or an automated webhook worker. 

You want:
1. **Machine authentication**: No user passwords or session cookies.
2. **Instant revocation**: If the partner accidentally leaks their API key, you can invalidate it with one click.
3. **Audit visibility**: Record every request, client IP, and timestamp.
4. **Zero credential plumbing**: No custom token generators or bcrypt migrations.

Let's build this in 5 simple steps.

---

## Step 1: Issue an API Token

You can generate tokens using either the terminal or the Django Admin.

=== "Terminal (CLI)"

    Run the `create_token` management command:

    ```bash
    python manage.py create_token --name "Partner Integration" --days 90
    ```

    Output:

    ```text
    Token created successfully!
    --------------------------------------------------------------------------------
    Prefix:     tok_demo1234
    Secret:     tok_demo1234:7f3a9e2b10cd4a5e6f7890abcdef12345678901234567890123456789012345678
    Expires At: 2026-12-02 14:00:00 UTC
    --------------------------------------------------------------------------------
    ```

    !!! tip "Assigning a User"
        To link this token to a specific Django user account, add `--user <username>`:
        ```bash
        python manage.py create_token --name "Partner Integration" --user partner_bot
        ```

=== "Django Admin"

    1. Navigate to your Django Admin (`http://localhost:8000/admin/`).
    2. Under **Keysmith**, click **Tokens** &rarr; **Add Token**.
    3. Fill in the **Name** (e.g., `Partner Integration`), select a **User**, and set an expiration date.
    4. Click **Save**.
    5. A one-time banner will display the raw token secret. Copy and save it immediately.

---

## Step 2: Protect an Endpoint

Now let's write an API view that requires this token.

=== "Django REST Framework (DRF)"

    ```python
    # myapp/views.py
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from keysmith.drf.permissions import RequireKeysmithToken

    class PartnerWebhookView(APIView):
        permission_classes = [RequireKeysmithToken]

        def get(self, request):
            return Response({
                "message": "Authenticated successfully!",
                "token_prefix": request.auth.prefix,
                "client_user": str(request.user),
            })
    ```

    Add the route to your `urls.py`:

    ```python
    # myapp/urls.py
    from django.urls import path
    from .views import PartnerWebhookView

    urlpatterns = [
        path("api/partner/", PartnerWebhookView.as_view(), name="partner-webhook"),
    ]
    ```

=== "Standard Django Views"

    ```python
    # myapp/views.py
    from django.http import JsonResponse
    from keysmith.django.decorator import keysmith_required

    @keysmith_required
    def partner_webhook(request):
        return JsonResponse({
            "message": "Authenticated successfully!",
            "token_prefix": request.keysmith_token.prefix,
            "client_user": str(request.keysmith_user),
        })
    ```

    Add the route to your `urls.py`:

    ```python
    # myapp/urls.py
    from django.urls import path
    from .views import partner_webhook

    urlpatterns = [
        path("api/partner/", partner_webhook, name="partner-webhook"),
    ]
    ```

---

## Step 3: Make an Authenticated Request

Send the token using the standard HTTP `Authorization` header with the `Bearer` scheme.

=== "cURL"

    ```bash
    curl -i http://localhost:8000/api/partner/ \
      -H "Authorization: Bearer <YOUR_RAW_TOKEN>"
    ```

=== "Python (HTTPX)"

    ```python
    import httpx

    token = "<YOUR_RAW_TOKEN>"
    headers = {"Authorization": f"Bearer {token}"}

    response = httpx.get("http://localhost:8000/api/partner/", headers=headers)
    print(response.status_code)
    print(response.json())
    ```

=== "HTTPie"

    ```bash
    http GET http://localhost:8000/api/partner/ \
      "Authorization: Bearer <YOUR_RAW_TOKEN>"
    ```

### Expected Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Authenticated successfully!",
  "token_prefix": "tok_demo1234",
  "client_user": "partner_bot"
}
```

### What Happens Without a Token?

If a client makes a request with a missing or invalid token:

```bash
curl -i http://localhost:8000/api/partner/
```

Response:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api"
Content-Type: application/json

{
  "detail": "Authentication credentials were not provided."
}
```

---

## Step 4: View the Audit Trail

Open your Django Admin and click **Token audit logs**.

Every request is logged automatically:
- **Action**: `authenticated` or `auth_failed`
- **Path & Method**: `GET /api/partner/`
- **Status Code**: `200` (or `401`)
- **Client IP Address**: Automatically resolved from socket or reverse proxies
- **User Agent & Timestamp**: Full diagnostic tracking

---

## Step 5: Rotate a Token (Zero-Downtime)

What if the partner accidentally commits their key to a public GitHub repository? You need to rotate the credential.

=== "Via Django Admin"

    1. Go to **Keysmith** &rarr; **Tokens** &rarr; Select your token.
    2. Click **Rotate token**.
    3. An explicit confirmation screen displays: *"Are you sure you want to rotate this token?"*
    4. Click **Confirm Rotation**.
    5. The new raw secret is displayed. Hand this to your partner. The old secret is immediately invalidated!

=== "Via Python Service"

    ```python
    from keysmith.models import Token
    from keysmith.services.tokens import rotate_token

    token = Token.objects.get(prefix="tok_demo1234")

    # Rotate the secret and receive the new raw token string
    new_raw_token = rotate_token(token)
    print(f"New secret: {new_raw_token}")
    ```

---

## Summary

You now have:
- A secure, database-backed API key pipeline.
- Instant rejection of forged tokens via CRC32 checksums.
- Real-time audit logs for compliance and debugging.
- Safe lifecycle tools (create, rotate, revoke).

**Next Steps:**
- Read **[Tokens](../topics/tokens.md)** to learn about system tokens, purging, and hash backends.
- Read **[Scopes](../topics/scopes.md)** to restrict tokens to specific CRUD actions.
- Read **[DRF Integration](../integrations/drf.md)** to set up rate throttling.
