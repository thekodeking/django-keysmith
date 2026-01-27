class TokenAuthError(Exception):
    """Base class for token authentication errors."""


class InvalidToken(TokenAuthError):
    """Token is malformed or does not exist."""


class RevokedToken(TokenAuthError):
    """Token has been revoked or purged."""


class ExpiredToken(TokenAuthError):
    """Token has expired."""
