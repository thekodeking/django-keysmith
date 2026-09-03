from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework.authentication import BaseAuthentication
    from rest_framework.exceptions import AuthenticationFailed, Throttled
    from rest_framework.settings import api_settings
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

    def authenticate_header(self, request) -> str:
        """Return WWW-Authenticate challenge scheme per RFC 9110."""
        scheme = getattr(keysmith_settings, "WWW_AUTHENTICATE_SCHEME", "Bearer")
        return f'{scheme} realm="api"' if "realm" not in scheme else scheme

    def _extract_from_header(self, raw_header: str | None) -> str | None:
        if not raw_header:
            return None
        cleaned = raw_header.strip()
        auth_types = tuple(getattr(keysmith_settings, "AUTH_HEADER_TYPES", ("Bearer", "Token")) or ())
        for auth_type in auth_types:
            prefix = f"{auth_type} "
            if cleaned.lower().startswith(prefix.lower()):
                return cleaned[len(prefix) :].strip()
        return cleaned

    def authenticate(self, request):
        # prevent duplicate audit records when middleware is also enabled.
        if hasattr(request, "_request"):
            request._request._keysmith_skip_middleware_audit = True

        header_name = keysmith_settings.HEADER_NAME.replace("HTTP_", "").replace("_", "-")
        raw = request.headers.get(header_name)
        if raw:
            raw = self._extract_from_header(raw)

        if not raw and header_name.lower() != "authorization":
            auth_header = request.headers.get("Authorization")
            if auth_header:
                extracted = self._extract_from_header(auth_header)
                if extracted and extracted != auth_header.strip():
                    raw = extracted

        if not raw and keysmith_settings.ALLOW_QUERY_PARAM:
            raw = request.query_params.get(keysmith_settings.QUERY_PARAM_NAME)
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
        user = token.user
        if user is None:
            unauthenticated_user = api_settings.UNAUTHENTICATED_USER
            user = (
                unauthenticated_user() if callable(unauthenticated_user) else unauthenticated_user
            )

        return (user, token)


__all__ = ["KeysmithAuthentication"]
