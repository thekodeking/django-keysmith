from keysmith.audit.logger import log_audit_event
from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import TokenAuthError
from keysmith.hooks import load_hook
from keysmith.settings import keysmith_settings


class KeysmithAuthenticationMiddleware:
    """Attach Keysmith auth context to each request and emit audit events."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.keysmith_token = None
        request.keysmith_user = None
        request.keysmith_auth_error = None
        request._keysmith_audit_state = None

        raw_token = self._get_raw_token(request)
        if raw_token:
            try:
                rate_limit_hook = load_hook("RATE_LIMIT_HOOK")
                if rate_limit_hook is not None:
                    rate_limit_hook(request=request, raw_token=raw_token)

                token = authenticate_token(raw_token)
            except TokenAuthError as exc:
                request.keysmith_auth_error = exc
                request._keysmith_audit_state = {
                    "success": False,
                    "error_code": exc.__class__.__name__.lower(),
                }
            else:
                request.keysmith_token = token
                request.keysmith_user = token.user
                request._keysmith_audit_state = {
                    "success": True,
                    "token": token,
                }

        response = self.get_response(request)

        if getattr(request, "_keysmith_skip_middleware_audit", False):
            return response

        state = getattr(request, "_keysmith_audit_state", None)
        if not state:
            if getattr(request, "_keysmith_auth_required", False) and not getattr(
                request, "keysmith_token", None
            ):
                log_audit_event(
                    action="auth_failed",
                    request=request,
                    status_code=response.status_code,
                    extra={"error_code": "missing_token"},
                )
            return response

        if state["success"]:
            log_audit_event(
                action="auth_success",
                request=request,
                token=state["token"],
                status_code=response.status_code,
            )
        else:
            log_audit_event(
                action="auth_failed",
                request=request,
                status_code=response.status_code,
                extra={"error_code": state["error_code"]},
            )

        return response

    def _get_raw_token(self, request) -> str | None:
        header_name: str = keysmith_settings.HEADER_NAME
        raw = request.META.get(header_name)

        if raw:
            return raw.strip()

        if keysmith_settings.ALLOW_QUERY_PARAM:
            return request.GET.get(keysmith_settings.QUERY_PARAM_NAME)

        return None
