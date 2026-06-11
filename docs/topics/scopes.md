# Scopes

Scopes control authorization - what an authenticated token is allowed to do. They are Django `Permission` codenames attached to each token via a many-to-many relationship.

Authentication answers *who* (or *which credential*). Scopes answer *what it may do*.

---

## Assigning scopes

Pass `Permission` instances when creating a token:

```python
from django.contrib.auth.models import Permission
from keysmith.services.tokens import create_token

write = Permission.objects.get(codename="add_post")

token, raw = create_token(name="writer", user=user, scopes=[write])
```

When `scopes` is omitted, `DEFAULT_SCOPES` from settings is applied automatically.

### Codename formats

At creation time, scopes accept two formats:

| Format | Example | When to use |
| --- | --- | --- |
| Bare codename | `"write"` | Single app, no collisions |
| Qualified | `"myapp.can_write"` | Multiple apps sharing codenames |

Configure an allowlist to prevent over-permissioning:

```python
KEYSMITH = {
    "AVAILABLE_SCOPES": ["read", "write", "admin"],
    "DEFAULT_SCOPES": ["read"],
}
```

Keysmith rejects any scope outside `AVAILABLE_SCOPES` at token creation.

!!! note "Runtime checks use codenames only"
    Scope enforcement at request time compares **permission codenames**, not `app_label.codename` qualifiers. Use distinct codenames across apps, or ensure codenames are unique within your permission set.

---

## Enforcing scopes

=== "Django"

    ```python
    from keysmith.django.decorator import keysmith_required
    from keysmith.django.permissions import keysmith_scopes

    @keysmith_required
    @keysmith_scopes("write")
    def create_post(request):
        ...
    ```

    | Outcome | HTTP status |
    | --- | --- |
    | No token | 401 |
    | Token missing scope | 403 (`PermissionDenied`) |

=== "DRF"

    ```python
    from keysmith.drf.permissions import RequireKeysmithToken, ScopedPermission

    class PostView(APIView):
        permission_classes = [RequireKeysmithToken, ScopedPermission("write")]
    ```

    `ScopedPermission("read", "write")` requires **all** listed scopes (AND logic).

    For reusable classes:

    ```python
    from keysmith.drf.permissions import HasKeysmithScopes

    class RequireWrite(HasKeysmithScopes):
        required_scopes = {"write"}
    ```

    Or declare scopes on the view:

    ```python
    class PostView(APIView):
        permission_classes = [RequireKeysmithToken, HasKeysmithScopes]
        required_scopes = {"write"}
    ```

Always require authentication (`@keysmith_required` or `RequireKeysmithToken`) **before** scope checks.

---

## Debugging

Inspect a token's scopes in a view:

=== "Django"

    ```python
    codenames = set(
        request.keysmith_token.scopes.values_list("codename", flat=True)
    )
    ```

=== "DRF"

    ```python
    codenames = set(
        request.auth.scopes.values_list("codename", flat=True)
    )
    ```

---

## Design guidance

| Practice | Rationale |
| --- | --- |
| Action-oriented names (`read`, `write`) | Easy to reason about |
| Least privilege defaults | Empty `DEFAULT_SCOPES`, assign explicitly |
| One token per client/system | Limits blast radius on compromise |
| `AVAILABLE_SCOPES` in production | Prevents accidental scope escalation |

---

**See also:** [Settings - scopes](settings.md#scopes) · [Permissions reference](../reference/permissions.md)
