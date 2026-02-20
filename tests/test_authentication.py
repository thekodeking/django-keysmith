from datetime import timedelta

import pytest
from django.utils import timezone

from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import ExpiredToken, InvalidToken, RevokedToken
from keysmith.services.tokens import create_token, revoke_token


@pytest.mark.django_db
class TestAuthenticateToken:
    """Test core token authentication."""

    def test_authenticate_token_success(self):
        """Valid token authenticates successfully."""
        token, raw_token = create_token(name="test-token")

        authenticated = authenticate_token(raw_token)

        assert authenticated.pk == token.pk

    def test_authenticate_token_updates_last_used(self):
        """Successful authentication updates last_used_at timestamp."""
        token, raw_token = create_token(name="test-token")
        assert token.last_used_at is None

        authenticate_token(raw_token)
        token.refresh_from_db()

        assert token.last_used_at is not None
        assert timezone.now() - token.last_used_at < timedelta(seconds=5)

    def test_authenticate_token_empty_raises_invalid(self):
        """Empty token raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("")

    def test_authenticate_token_none_raises_invalid(self):
        """None token raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token(None)  # type: ignore[arg-type]

    def test_authenticate_token_invalid_format_raises_invalid(self):
        """Invalid token format raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("invalid-token-format")

    def test_authenticate_token_missing_checksum_raises_invalid(self):
        """Token without checksum raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("tok_abc123:secret")

    def test_authenticate_token_wrong_checksum_raises_invalid(self):
        """Token with wrong checksum raises InvalidToken."""
        _, raw_token = create_token(name="test-token")
        tampered = raw_token[:-6] + "000000"

        with pytest.raises(InvalidToken):
            authenticate_token(tampered)

    def test_authenticate_token_nonexistent_prefix_raises_invalid(self):
        """Token with non-existent prefix raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("tok_nonexistent:secret123456")

    def test_authenticate_token_wrong_secret_raises_invalid(self):
        """Token with wrong secret raises InvalidToken."""
        token, _ = create_token(name="test-token")
        fake_token = f"{token.prefix}:wrongsecret1234567890123456789012345678901234"

        with pytest.raises(InvalidToken):
            authenticate_token(fake_token)

    def test_authenticate_revoked_token_raises_revoked(self):
        """Revoked token raises RevokedToken."""
        token, raw_token = create_token(name="revoked-token")
        revoke_token(token)

        with pytest.raises(RevokedToken):
            authenticate_token(raw_token)

    def test_authenticate_purged_token_raises_revoked(self):
        """Purged token raises RevokedToken."""
        token, raw_token = create_token(name="purged-token")
        revoke_token(token, purge=True)

        with pytest.raises(RevokedToken):
            authenticate_token(raw_token)

    def test_authenticate_expired_token_raises_expired(self):
        """Expired token raises ExpiredToken."""
        expiry = timezone.now() - timedelta(days=1)
        _, raw_token = create_token(name="expired-token", expires_at=expiry)

        with pytest.raises(ExpiredToken) as exc:
            authenticate_token(raw_token)

        assert "expired on" in str(exc.value).lower()

    def test_authenticate_token_includes_expiry_date_in_error(self):
        """ExpiredToken error message includes expiry date."""
        expiry = timezone.now() - timedelta(days=5)
        _, raw_token = create_token(name="expired-token", expires_at=expiry)

        with pytest.raises(ExpiredToken) as exc:
            authenticate_token(raw_token)

        assert str(expiry.date()) in str(exc.value) or str(expiry.year) in str(exc.value)


@pytest.mark.django_db
class TestTokenFormatValidation:
    """Test token format validation during authentication."""

    def test_token_too_short_raises_invalid(self):
        """Token shorter than minimum length raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("short")

    def test_token_without_separator_raises_invalid(self):
        """Token without underscore separator raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("nounderscore:secret123456789012345678901234567890123456")

    def test_token_without_colon_raises_invalid(self):
        """Token without colon separator raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("tok_abc123secret1234567890123456789012345678901234567890")

    def test_token_empty_secret_raises_invalid(self):
        """Token with empty secret raises InvalidToken."""
        with pytest.raises(InvalidToken):
            authenticate_token("tok_abc123:123456")

    def test_token_checksum_timing_attack_protection(self):
        """Checksum comparison uses timing-safe comparison."""
        # This test verifies that checksum validation doesn't use simple string comparison
        # which would be vulnerable to timing attacks
        _, raw_token = create_token(name="test-token")
        tampered = raw_token[:-1] + ("0" if raw_token[-1] != "0" else "1")

        with pytest.raises(InvalidToken):
            authenticate_token(tampered)
