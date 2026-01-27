from django.db import transaction

from keysmith.models import Token
from keysmith.hashers.base import BaseTokenHasher
from keysmith.settings import keysmith_settings
from keysmith.services.tokens import mark_token_used
from keysmith.utils.tokens import extract_prefix_and_secret
from keysmith.auth.exceptions import (
    InvalidToken,
    RevokedToken,
    ExpiredToken,
)
from keysmith.hashers.registry import get_hasher


@transaction.atomic
def authenticate_token(raw_token: str) -> Token:
    """
    Authenticate a public token string and return the Token instance.

    Raises:
        InvalidToken
        RevokedToken
        ExpiredToken
    """
    if not raw_token:
        raise InvalidToken("Empty token")

    try:
        prefix, secret = extract_prefix_and_secret(raw_token)
    except ValueError as exc:
        raise InvalidToken(str(exc)) from exc

    try:
        token = Token.objects.select_for_update().get(prefix=prefix)
    except Token.DoesNotExist:
        raise InvalidToken("Invalid token")

    if token.revoked or token.purged:
        raise RevokedToken("Token has been revoked")

    if token.is_expired:
        raise ExpiredToken("Token has expired")

    hasher: BaseTokenHasher = get_hasher()
    if not hasher.verify(secret, token.key):
        raise InvalidToken("Invalid token")

    mark_token_used(token)
    return token
