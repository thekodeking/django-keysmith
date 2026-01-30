from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import TokenAuthError
from keysmith.settings import keysmith_settings


class KeysmithAuthentication(BaseAuthentication):
    """
    DRF authentication backend for Keysmith tokens.
    """

    def authenticate(self, request):
        raw = request.headers.get(keysmith_settings.HEADER_NAME)
        if not raw:
            return None

        try:
            token = authenticate_token(raw.strip())
        except TokenAuthError as exc:
            raise AuthenticationFailed("Invalid or expired token") from exc

        return (token.user, token)
