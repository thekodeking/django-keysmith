from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework.exceptions import PermissionDenied
    from rest_framework.permissions import BasePermission
except Exception as exc:
    raise ImproperlyConfigured(
        "Keysmith DRF permissions require installing django-keysmith[drf]."
    ) from exc

from keysmith.auth.utils import get_message


class HasKeysmithScopes(BasePermission):
    """
    Require Keysmith scopes in DRF views.
    """

    required_scopes: set[str] = set()

    def has_permission(self, request, view) -> bool:
        token = getattr(request, "auth", None)

        if not token:
            return False

        token_scopes_field = getattr(token, "scopes", None)
        if hasattr(token_scopes_field, "values_list"):
            token_scopes = set(token_scopes_field.values_list("codename", flat=True))
        else:
            token_scopes = set(token_scopes_field or [])
        missing = self.required_scopes - token_scopes

        if missing:
            raise PermissionDenied(get_message("insufficient_scope"))

        return True


class ScopedPermission(HasKeysmithScopes):
    def __init__(self, *scopes: str):
        self.required_scopes = set(scopes)


__all__ = ["HasKeysmithScopes", "ScopedPermission"]
