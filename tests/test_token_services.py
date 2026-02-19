from datetime import timedelta

import pytest
from django.utils import timezone

from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import ExpiredToken, InvalidToken, RevokedToken
from keysmith.models import Token, TokenAuditLog
from keysmith.services.tokens import create_token, revoke_token, rotate_token


@pytest.mark.django_db
class TestCreateToken:
    """Test token creation service."""

    def test_create_token_returns_token_and_raw_token(self):
        """Creating a token returns both the token object and raw token string."""
        token, raw_token = create_token(name="test-token")

        assert isinstance(token, Token)
        assert isinstance(raw_token, str)
        assert len(raw_token) > 0
        assert "_" in raw_token
        assert ":" in raw_token

    def test_create_token_stores_hashed_secret(self):
        """Only the hashed secret is stored in the database."""
        token, raw_token = create_token(name="test-token")

        # Raw token should not be stored
        assert raw_token not in token.key
        # Key should be hashed
        assert token.key.startswith("pbkdf2_sha512$")

    def test_create_token_generates_unique_prefix(self):
        """Each token gets a unique prefix."""
        token1, _ = create_token(name="token-1")
        token2, _ = create_token(name="token-2")

        assert token1.prefix != token2.prefix
        assert token1.prefix.startswith("tok_")
        assert token2.prefix.startswith("tok_")

    def test_create_token_with_description(self):
        """Token can be created with a description."""
        token, _ = create_token(name="test-token", description="Test description")

        assert token.description == "Test description"

    def test_create_token_with_expiry(self):
        """Token can be created with a custom expiry date."""
        expiry = timezone.now() + timedelta(days=30)
        token, _ = create_token(name="test-token", expires_at=expiry)

        assert token.expires_at == expiry

    def test_create_token_default_expiry(self):
        """Token gets default expiry from settings."""
        token, _ = create_token(name="test-token")

        assert token.expires_at is not None
        expected_expiry = timezone.now() + timedelta(days=90)
        # Allow for small time difference during test execution
        assert abs((token.expires_at - expected_expiry).total_seconds()) < 5

    def test_create_token_without_expiry(self):
        """Token can be created without expiry if DEFAULT_EXPIRY_DAYS is None."""
        with pytest.MonkeyPatch.context() as mp:
            from keysmith import settings as ks_settings

            mp.setattr(ks_settings.keysmith_settings, "DEFAULT_EXPIRY_DAYS", None)

            token, _ = create_token(name="test-token")
            assert token.expires_at is None

    def test_create_token_with_scopes(self, django_db_blocker):
        """Token can be created with permission scopes."""
        from django.contrib.auth.models import Permission

        with django_db_blocker.unblock():
            permission = Permission.objects.first()
            if permission:
                token, _ = create_token(name="test-token", scopes=[permission])
                assert token.scopes.filter(pk=permission.pk).exists()

    def test_create_token_sets_timestamps(self):
        """Token creation sets created_at timestamp."""
        before = timezone.now()
        token, _ = create_token(name="test-token")
        after = timezone.now()

        assert before <= token.created_at <= after

    def test_create_token_name_required(self):
        """Token name is a required parameter."""
        with pytest.raises(TypeError):
            create_token()  # pylint: disable=no-value-for-parameter


@pytest.mark.django_db
class TestRevokeToken:
    """Test token revocation service."""

    def test_revoke_token_marks_revoked(self):
        """Revoking a token marks it as revoked."""
        token, raw_token = create_token(name="test-token")
        assert not token.revoked

        revoke_token(token)
        token.refresh_from_db()

        assert token.revoked

    def test_revoke_token_logs_audit_event(self):
        """Revoking a token creates an audit log entry."""
        token, _ = create_token(name="test-token")

        revoke_token(token)

        audit_log = TokenAuditLog.objects.filter(
            token=token, action=TokenAuditLog.ACTION_REVOKED
        ).first()
        assert audit_log is not None
        assert audit_log.extra.get("purge") is False

    def test_revoke_token_with_purge(self):
        """Revoking with purge also marks token as purged."""
        token, _ = create_token(name="test-token")

        revoke_token(token, purge=True)
        token.refresh_from_db()

        assert token.revoked
        assert token.purged

    def test_revoke_token_logs_purge_in_audit(self):
        """Revoke with purge includes purge flag in audit log."""
        token, _ = create_token(name="test-token")

        revoke_token(token, purge=True)

        audit_log = TokenAuditLog.objects.filter(
            token=token, action=TokenAuditLog.ACTION_REVOKED
        ).first()
        assert audit_log.extra.get("purge") is True

    def test_revoke_already_revoked_token_no_duplicate_log(self):
        """Revoking an already revoked token doesn't duplicate audit logs."""
        token, _ = create_token(name="test-token")
        revoke_token(token)
        initial_count = TokenAuditLog.objects.filter(
            token=token, action=TokenAuditLog.ACTION_REVOKED
        ).count()

        revoke_token(token)
        final_count = TokenAuditLog.objects.filter(
            token=token, action=TokenAuditLog.ACTION_REVOKED
        ).count()

        assert initial_count == final_count


@pytest.mark.django_db
class TestRotateToken:
    """Test token rotation service."""

    def test_rotate_token_generates_new_secret(self):
        """Rotating a token generates a new secret."""
        token, old_raw_token = create_token(name="test-token")
        old_key = token.key

        new_raw_token = rotate_token(token)
        token.refresh_from_db()

        assert new_raw_token != old_raw_token
        assert token.key != old_key

    def test_rotate_token_returns_valid_token(self):
        """Rotated token can be authenticated."""
        token, _ = create_token(name="test-token")
        new_raw_token = rotate_token(token)

        # Should authenticate successfully
        authenticated = authenticate_token(new_raw_token)
        assert authenticated.pk == token.pk

    def test_rotate_token_invalidates_old_token(self):
        """Old token is invalidated after rotation."""
        token, old_raw_token = create_token(name="test-token")
        rotate_token(token)

        # Old token should fail authentication
        with pytest.raises(InvalidToken):
            authenticate_token(old_raw_token)

    def test_rotate_token_logs_audit_event(self):
        """Rotating a token creates an audit log entry."""
        token, _ = create_token(name="test-token")

        rotate_token(token)

        audit_log = TokenAuditLog.objects.filter(
            token=token, action=TokenAuditLog.ACTION_ROTATED
        ).first()
        assert audit_log is not None

    def test_rotate_token_clears_last_used(self):
        """Rotating a token clears the last_used_at timestamp."""
        token, raw_token = create_token(name="test-token")
        authenticate_token(raw_token)  # Sets last_used_at
        token.refresh_from_db()
        assert token.last_used_at is not None

        rotate_token(token)
        token.refresh_from_db()

        assert token.last_used_at is None

    def test_rotate_revoked_token_raises_error(self):
        """Cannot rotate a revoked token."""
        token, _ = create_token(name="test-token")
        revoke_token(token)

        with pytest.raises(ValueError, match="Cannot rotate a revoked"):
            rotate_token(token)

    def test_rotate_purged_token_raises_error(self):
        """Cannot rotate a purged token."""
        token, _ = create_token(name="test-token")
        revoke_token(token, purge=True)

        with pytest.raises(ValueError, match="Cannot rotate a revoked"):
            rotate_token(token)


@pytest.mark.django_db
class TestTokenLifecycleIntegration:
    """Integration tests for complete token lifecycle."""

    def test_full_token_lifecycle(self):
        """Test complete lifecycle: create -> authenticate -> rotate -> authenticate -> revoke."""
        # Create token
        token, raw_token = create_token(name="lifecycle-test")
        assert not token.revoked

        # Authenticate
        authenticated = authenticate_token(raw_token)
        assert authenticated.pk == token.pk

        # Rotate
        new_raw_token = rotate_token(token)
        assert new_raw_token != raw_token

        # Old token should fail
        with pytest.raises(InvalidToken):
            authenticate_token(raw_token)

        # New token should work
        authenticated = authenticate_token(new_raw_token)
        assert authenticated.pk == token.pk

        # Revoke
        revoke_token(token)
        token.refresh_from_db()
        assert token.revoked

        # Revoked token should fail
        with pytest.raises(RevokedToken):
            authenticate_token(new_raw_token)

    def test_expired_token_cannot_authenticate(self):
        """Expired tokens cannot be authenticated."""
        expiry = timezone.now() - timedelta(days=1)
        token, raw_token = create_token(name="expired-token", expires_at=expiry)

        with pytest.raises(ExpiredToken):
            authenticate_token(raw_token)

    def test_token_properties(self):
        """Test token is_active and is_expired properties."""
        # Active token
        token, _ = create_token(name="active-token")
        assert token.is_active
        assert not token.is_expired

        # Expired token
        token.expires_at = timezone.now() - timedelta(days=1)
        assert not token.is_active
        assert token.is_expired

        # Revoked token
        token, _ = create_token(name="revoked-token")
        revoke_token(token)
        token.refresh_from_db()
        assert not token.is_active

        # Purged token
        token, _ = create_token(name="purged-token")
        revoke_token(token, purge=True)
        token.refresh_from_db()
        assert not token.is_active
