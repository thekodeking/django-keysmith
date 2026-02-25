from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework.exceptions import NotAuthenticated, PermissionDenied
    from rest_framework.permissions import BasePermission
except Exception as exc:
    raise ImproperlyConfigured(
        "Keysmith DRF permissions require installing django-keysmith[drf]."
    ) from exc

from keysmith.audit.logger import log_audit_event
from keysmith.auth.utils import get_message


class RequireKeysmithToken(BasePermission):
    """
    Require a successfully authenticated Keysmith token.
    """

    def has_permission(self, request, view) -> bool:
        token = getattr(request, "auth", None)
        if token:
            return True

        log_audit_event(
            action="auth_failed",
            request=request,
            status_code=401,
            extra={"error_code": "missing_token"},
        )
        raise NotAuthenticated(get_message("missing_token"))


class HasKeysmithScopes(BasePermission):
    """
    Require Keysmith scopes in DRF views.
    """

    required_scopes: set[str] = set()

    def _required_scopes_for_view(self, view) -> set[str]:
        raw_scopes = getattr(view, "required_scopes", self.required_scopes)
        if isinstance(raw_scopes, str):
            return {raw_scopes}
        return set(raw_scopes or [])

    def has_permission(self, request, view) -> bool:
        token = getattr(request, "auth", None)

        if not token:
            return False

        required_scopes = self._required_scopes_for_view(view)
        if not required_scopes:
            return True

        token_scopes_field = getattr(token, "scopes", None)
        if hasattr(token_scopes_field, "values_list"):
            token_scopes = set(token_scopes_field.values_list("codename", flat=True))
        else:
            token_scopes = set(token_scopes_field or [])
        missing = required_scopes - token_scopes

        if missing:
            raise PermissionDenied(get_message("insufficient_scope"))

        return True


class ScopedPermission(HasKeysmithScopes):
    def __init__(self, *scopes: str):
        self.required_scopes = set(scopes)


__all__ = ["RequireKeysmithToken", "HasKeysmithScopes", "ScopedPermission"]
