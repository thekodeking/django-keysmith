# Scopes & Permissions

Restrict what each token can do by assigning fine-grained permission scopes.

---

## Why Use Scopes?

Not all API clients need full access to your API:

- A **Read-Only Dashboard** needs `reports.view_analytics`.
- A **Billing Webhook** needs `invoices.change_invoice`.
- A **Monitoring Agent** only needs `health.view_metrics`.

Instead of inventing a custom permission system, **Keysmith reuses Django's standard `django.contrib.auth.models.Permission` model**. This means your tokens, human users, and Django Admin all speak the exact same permission language!

---

## 1. Configuring Scopes

In your `settings.py`, register the permission codenames available for token issuance:

```python
# settings.py

KEYSMITH = {
    # All scopes that can be granted to tokens:
    "AVAILABLE_SCOPES": [
        "orders.view_order",
        "orders.add_order",
        "orders.change_order",
        "reports.view_analytics",
    ],
    # Default scopes automatically assigned if none are specified:
    "DEFAULT_SCOPES": [
        "orders.view_order",
    ],
}
```

Format is `<app_label>.<permission_codename>`.

---

## 2. Issuing Scoped Tokens

=== "CLI"

    Pass comma-separated codenames to the `--scopes` flag:

    ```bash
    python manage.py create_token \
      --name "Order Sync Worker" \
      --scopes "orders.view_order,orders.add_order"
    ```

=== "Python"

    Pass a list of `Permission` objects or string codenames:

    ```python
    from keysmith.services.tokens import create_token

    token, raw = create_token(
        name="Order Sync Worker",
        scopes=["orders.view_order", "orders.add_order"],
    )
    ```

=== "Django Admin"

    When creating or editing a token in the Django Admin, select the desired scopes from the filter horizontal widget.

---

## 3. Enforcing Scopes on Views

### In Django REST Framework (DRF)

Use the `HasTokenScope` permission class:

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from keysmith.drf.permissions import RequireKeysmithToken, HasTokenScope

class CreateOrderView(APIView):
    # Requires valid token AND the 'orders.add_order' scope
    permission_classes = [RequireKeysmithToken, HasTokenScope]
    required_scopes = ["orders.add_order"]

    def post(self, request):
        return Response({"status": "order created"})
```

### In Standard Django Views

Use the `@require_scopes` decorator:

```python
# views.py
from django.http import JsonResponse
from keysmith.django.decorator import keysmith_required, require_scopes

@keysmith_required
@require_scopes("orders.add_order")
def create_order(request):
    return JsonResponse({"status": "order created"})
```

If a token is authenticated but lacks the required scope, Keysmith returns:

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Token does not have required scope: orders.add_order"
}
```

---

## Inspecting Scopes at Runtime

You can inspect a token's scopes directly inside your views:

=== "DRF"

    ```python
    class OrderView(APIView):
        def get(self, request):
            token = request.auth
            
            # Check a specific scope:
            can_delete = token.has_scope("orders.delete_order")
            
            # List all assigned scopes:
            all_scopes = [f"{s.content_type.app_label}.{s.codename}" for s in token.scopes.all()]
            
            return Response({"can_delete": can_delete, "scopes": all_scopes})
    ```

=== "Standard Django"

    ```python
    @keysmith_required
    def order_view(request):
        token = request.keysmith_token
        
        can_delete = token.has_scope("orders.delete_order")
        return JsonResponse({"can_delete": can_delete})
    ```
