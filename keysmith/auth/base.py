from django.db import transaction

from keysmith.auth.exceptions import (
    ExpiredToken,
    InvalidToken,
    RevokedToken,
)
from keysmith.hashers.base import BaseTokenHasher
from keysmith.hashers.registry import get_hasher
from keysmith.models.utils import get_token_model
from keysmith.services.tokens import mark_token_used
from keysmith.utils.tokens import extract_prefix_and_secret


@transaction.atomic
def authenticate_token(raw_token: str):
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
        Token = get_token_model()
        token = Token.objects.select_for_update().get(prefix=prefix)
    except Token.DoesNotExist as exc:
        raise InvalidToken("Invalid token") from exc

    if token.revoked or token.purged:
        raise RevokedToken("Token has been revoked")

    if token.is_expired:
        raise ExpiredToken("Token has expired")

    hasher: BaseTokenHasher = get_hasher()
    if not hasher.verify(secret, token.key):
        raise InvalidToken("Invalid token")

    mark_token_used(token)
    return token
