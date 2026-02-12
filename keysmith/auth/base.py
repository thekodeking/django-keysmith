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
    Authenticate a user's token and return the Token instance if valid.
    
    This function verifies that the provided token exists, hasn't been revoked,
    hasn't expired, and matches the stored hash. If authentication succeeds,
    the token's last-used timestamp is updated.
    
    Args:
        raw_token: The complete token string provided by the user
        
    Returns:
        Token: The authenticated token instance
        
    Raises:
        InvalidToken: When the token format is invalid, doesn't exist, or 
                     the secret doesn't match
        RevokedToken: When the token has been revoked or purged
        ExpiredToken: When the token has passed its expiration date
        
    Example:
        >>> token = authenticate_token("prefix_secretpart123456")
        >>> print(f"Authenticated token for user: {token.user}")
    """
    if not raw_token:
        raise InvalidToken(
            "No token provided. Please include a valid authentication token."
        )
    
    try:
        prefix, secret = extract_prefix_and_secret(raw_token)
    except ValueError as exc:
        raise InvalidToken(
            f"Token format is invalid: {exc}. Expected format: 'prefix_secret'"
        ) from exc
    
    try:
        Token = get_token_model()
        token = Token.objects.select_for_update().get(prefix=prefix)
    except Token.DoesNotExist as exc:
        raise InvalidToken(
            "This token doesn't exist or has been deleted. "
            "Please request a new token."
        ) from exc
    
    if token.revoked or token.purged:
        raise RevokedToken(
            "This token has been revoked and can no longer be used. "
            "Please request a new token to continue."
        )
    
    if token.is_expired:
        raise ExpiredToken(
            f"This token expired on {token.expiry_date}. "
            "Please request a new token to continue."
        )
    
    hasher: BaseTokenHasher = get_hasher()
    if not hasher.verify(secret, token.key):
        raise InvalidToken(
            "Authentication failed. The token provided is not valid. "
            "Please check your token and try again."
        )
    
    mark_token_used(token)
    return token
