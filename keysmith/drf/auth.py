from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework.authentication import BaseAuthentication
    from rest_framework.exceptions import AuthenticationFailed, Throttled
except Exception as exc:
    raise ImproperlyConfigured(
        "Keysmith DRF authentication requires installing django-keysmith[drf]."
    ) from exc

from keysmith.audit.logger import log_audit_event
from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import TokenAuthError
from keysmith.auth.utils import get_message
from keysmith.hooks import load_hook
from keysmith.settings import keysmith_settings


class KeysmithAuthentication(BaseAuthentication):
    """Authenticate DRF requests using Keysmith tokens from configured header."""

    def authenticate(self, request):
        # prevent duplicate audit records when middleware is also enabled.
        if hasattr(request, "_request"):
            request._request._keysmith_skip_middleware_audit = True

        header_name = keysmith_settings.HEADER_NAME.replace("HTTP_", "").replace("_", "-")
        raw = request.headers.get(header_name)
        if not raw:
            return None

        try:
            token = authenticate_token(raw.strip())
            throttle_hook = load_hook("DRF_THROTTLE_HOOK")
            if throttle_hook is not None:
                throttle_hook(request=request, token=token)
        except TokenAuthError as exc:
            log_audit_event(
                action="auth_failed",
                request=request,
                status_code=401,
                extra={"error_code": exc.__class__.__name__.lower()},
            )
            raise AuthenticationFailed(get_message("invalid_token")) from exc
        except Throttled:
            log_audit_event(
                action="auth_failed",
                request=request,
                status_code=429,
                extra={"error_code": "rate_limited"},
            )
            raise

        log_audit_event(
            action="auth_success",
            request=request,
            token=token,
            status_code=200,
        )
        return (token.user, token)


__all__ = ["KeysmithAuthentication"]
