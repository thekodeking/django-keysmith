from functools import wraps
from typing import Callable

from django.http import HttpRequest, HttpResponse

from keysmith.django.http import HttpResponseUnauthorized
from keysmith.auth.utils import get_message


def keysmith_required(
    view_func: Callable | None = None,
    *,
    allow_anonymous: bool = False,
    missing_message: str | None = None,
    invalid_message: str | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if getattr(request, "keysmith_user", None):
                return func(request, *args, **kwargs)

            if getattr(request, "keysmith_auth_error", None):
                return HttpResponseUnauthorized(
                    invalid_message or get_message("invalid_token")
                )

            if allow_anonymous:
                return func(request, *args, **kwargs)

            return HttpResponseUnauthorized(
                missing_message or get_message("missing_token")
            )

        return wrapped

    return decorator(view_func) if view_func else decorator
