# Permissions

---

## DRF

Module: `keysmith.drf.permissions`

### `RequireKeysmithToken`

```python
from keysmith.drf.permissions import RequireKeysmithToken
```

Requires `request.auth` to be a token instance.

- Missing → `NotAuthenticated` + `auth_failed` audit
- Present → passes

### `HasKeysmithScopes`

```python
from keysmith.drf.permissions import HasKeysmithScopes
```

Checks token scope codenames against `required_scopes`.

**Scope source precedence:**

1. `view.required_scopes` if defined
2. `permission.required_scopes` on the class/instance

- Missing scopes → `PermissionDenied`

```python
class RequireWrite(HasKeysmithScopes):
    required_scopes = {"write"}
```

### `ScopedPermission`

```python
from keysmith.drf.permissions import ScopedPermission

ScopedPermission("write", "admin")  # requires ALL scopes
```

---

## Django

Module: `keysmith.django.permissions`

### `keysmith_scopes`

```python
from keysmith.django.permissions import keysmith_scopes

@keysmith_required
@keysmith_scopes("write")
def view(request): ...

@keysmith_scopes("read", "write")  # requires ALL scopes
```

| Condition | Result |
| --- | --- |
| No `keysmith_token` | 401 unauthorized |
| Missing scope codename | `PermissionDenied` (403) |

Compares against `Permission.codename` values on the token's scopes M2M.
