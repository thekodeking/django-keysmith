# Permissions API

Permission helpers are split between DRF permission classes and plain Django decorators so each stack can stay idiomatic.

## DRF Permissions

### `RequireKeysmithToken`

This permission enforces that DRF authentication has produced a token object in `request.auth`.

```python
from keysmith.drf.permissions import RequireKeysmithToken
```

Requires a successfully authenticated token in `request.auth`.
Raises `NotAuthenticated` when missing.

### `HasKeysmithScopes`

This permission checks declared scopes against the token's permission codenames.

```python
from keysmith.drf.permissions import HasKeysmithScopes
```

Checks token scopes against `required_scopes` declared on the DRF view or permission.
Raises `PermissionDenied` if required scopes are missing.

Scope source precedence:

- `view.required_scopes` when defined on the DRF view
- otherwise `required_scopes` on the permission class/instance

Subclass usage:

```python
class RequireWriteScope(HasKeysmithScopes):
    required_scopes = {"write"}
```

View-level usage:

```python
from keysmith.drf.permissions import HasKeysmithScopes, RequireKeysmithToken

class WriteView(APIView):
    permission_classes = [RequireKeysmithToken, HasKeysmithScopes]
    required_scopes = {"write"}
```

### `ScopedPermission(*scopes)`

Use this class for inline per-view requirements when you don't need a reusable subclass.

```python
from keysmith.drf.permissions import ScopedPermission
```

Inline scope checks:

```python
permission_classes = [RequireKeysmithToken, ScopedPermission("write", "admin")]
```

## Django Decorator Permission

### `keysmith_scopes(*required_scopes)`

Use this decorator for scope checks in plain Django views.

```python
from keysmith.django.permissions import keysmith_scopes
```

Behavior:

- returns unauthorized response when token context is missing
- raises `django.core.exceptions.PermissionDenied` when scopes are missing

Example:

```python
from keysmith.django.decorator import keysmith_required

@keysmith_required
@keysmith_scopes("write")
def create_view(request):
    ...
```
