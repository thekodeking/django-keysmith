from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class HasKeysmithScopes(BasePermission):
    """
    Require Keysmith scopes in DRF views.
    """

    required_scopes: set[str] = set()

    def has_permission(self, request, view) -> bool:
        token = getattr(request, "auth", None)

        if not token:
            return False

        token_scopes = set(getattr(token, "scopes", []))
        missing = self.required_scopes - token_scopes

        if missing:
            # todo(thekodeking): update error message later
            raise PermissionDenied("Insufficient scope")

        return True


class ScopedPermission(HasKeysmithScopes):
    def __init__(self, *scopes: str):
        self.required_scopes = set(scopes)
