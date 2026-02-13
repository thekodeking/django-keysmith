"""Integration tests for Keysmith token authentication flows."""

from datetime import timedelta

import pytest
from django.utils import timezone

from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import ExpiredToken, InvalidToken, RevokedToken
from keysmith.services.tokens import create_token, revoke_token


@pytest.mark.django_db
def test_authenticate_token_success_updates_last_used() -> None:
    """Authenticating a valid token returns the model and stamps last-used time."""
    token, raw_token = create_token(name="test token")
    assert token.last_used_at is None

    authenticated = authenticate_token(raw_token)
    token.refresh_from_db()

    assert authenticated.pk == token.pk
    assert token.last_used_at is not None


@pytest.mark.django_db
def test_authenticate_token_expired_raises_expired_token() -> None:
    """Expired tokens should raise ExpiredToken instead of runtime attribute errors."""
    expired_at = timezone.now() - timedelta(days=1)
    _, raw_token = create_token(name="expired token", expires_at=expired_at)

    with pytest.raises(ExpiredToken) as exc:
        authenticate_token(raw_token)

    assert "expired on" in str(exc.value).lower()


@pytest.mark.django_db
def test_authenticate_token_revoked_raises_revoked_token() -> None:
    """Revoked tokens are rejected during authentication."""
    token, raw_token = create_token(name="revoked token")
    revoke_token(token)

    with pytest.raises(RevokedToken):
        authenticate_token(raw_token)


@pytest.mark.django_db
def test_authenticate_token_with_tampered_checksum_raises_invalid_token() -> None:
    """Any checksum mismatch should map to an InvalidToken auth error."""
    _, raw_token = create_token(name="valid token")
    tampered = raw_token[:-1] + ("0" if raw_token[-1] != "0" else "1")

    with pytest.raises(InvalidToken):
        authenticate_token(tampered)
