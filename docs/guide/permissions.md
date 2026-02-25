# Permissions and Scopes

Keysmith scopes are Django permission codenames associated with `token.scopes`. This makes scope management align with existing Django auth primitives.

## Assign Scopes During Token Creation

Attach scopes when creating tokens so authorization intent is explicit from day one.

```python
from django.contrib.auth.models import Permission
from keysmith.services.tokens import create_token

write_perm = Permission.objects.get(codename="write")

token, raw_token = create_token(
    name="writer-token",
    user=user,
    scopes=[write_perm],
)
```

## DRF Scope Enforcement

Always require authentication first to guarantee `request.auth` exists before scope checks run.

```python
from keysmith.drf.permissions import RequireKeysmithToken, ScopedPermission

permission_classes = [RequireKeysmithToken, ScopedPermission("write")]
```

`ScopedPermission("write", "admin")` requires all listed scopes.

For reusable permission classes, subclass `HasKeysmithScopes`:

```python
from keysmith.drf.permissions import HasKeysmithScopes

class RequireWriteScope(HasKeysmithScopes):
    required_scopes = {"write"}
```

You can also keep `HasKeysmithScopes` directly in `permission_classes` and declare
`required_scopes` on the view:

```python
from keysmith.drf.permissions import HasKeysmithScopes, RequireKeysmithToken

class WriteView(APIView):
    permission_classes = [RequireKeysmithToken, HasKeysmithScopes]
    required_scopes = {"write"}
```

## Plain Django Scope Enforcement

Use `keysmith_scopes` with `keysmith_required` for function-based or class-based plain Django views.

```python
from keysmith.django.decorator import keysmith_required
from keysmith.django.permissions import keysmith_scopes

@keysmith_required
@keysmith_scopes("write")
def create_resource(request):
    ...
```

Missing scopes raise `django.core.exceptions.PermissionDenied`.

## Debugging Scope Issues

In DRF views, `request.auth` points to the token object. Inspecting codename sets quickly reveals mismatches.

```python
token_scopes = set(request.auth.scopes.values_list("codename", flat=True))
print(token_scopes)
```

## Suggested Scope Design

Keep scope semantics simple and composable so policy stays understandable.

- Use action-oriented names: `read`, `write`, `admin`.
- Keep least privilege by default.
- Use separate tokens for separate systems.
