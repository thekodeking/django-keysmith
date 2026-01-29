from django.utils.deprecation import MiddlewareMixin

from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import TokenAuthError
from keysmith.models import Token
from keysmith.settings import keysmith_settings


class KeysmithAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        raw_token = self._get_raw_token(request)
        if not raw_token:
            request.keysmith_token = None
            request.keysmith_user = None
            return

        try:
            token: Token = authenticate_token(raw_token)
        except TokenAuthError:
            request.keysmith_token = None
            request.keysmith_user = None

            return

        request.keysmith_token = token
        request.keysmith_user = token.user

    def _get_raw_token(self, request) -> str | None:
        header_name: str = keysmith_settings.HEADER_NAME
        raw = request.META.get(header_name)

        if raw:
            return raw.strip()

        if keysmith_settings.ALLOW_QUERY_PARAM:
            return request.GET.get(keysmith_settings.QUERY_PARAM_NAME)

        return None
