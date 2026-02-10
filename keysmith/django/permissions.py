from functools import wraps
from typing import Callable

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from keysmith.django.http import HttpResponseUnauthorized
from keysmith.auth.utils import get_message


def keysmith_scopes(*required_scopes: str) -> Callable:
    """
    Require one or more Keysmith scopes.

    Usage:
        @keysmith_required
        @keysmith_scopes("tokens:read")
        def view(request): ...
    """

    required = set(required_scopes)

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            token = getattr(request, "keysmith_token", None)

            if not token:
                return HttpResponseUnauthorized(get_message("missing_token"))

            token_scopes_field = getattr(token, "scopes", None)
            if hasattr(token_scopes_field, "values_list"):
                token_scopes = set(
                    token_scopes_field.values_list("codename", flat=True)
                )
            else:
                token_scopes = set(token_scopes_field or [])
            missing = required - token_scopes

            if missing:
                raise PermissionDenied(get_message("insufficient_scope"))

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
