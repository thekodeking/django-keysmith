from datetime import timedelta

import pytest
from django.utils import timezone

from keysmith.models import Token, TokenAuditLog
from keysmith.services.tokens import create_token, revoke_token


@pytest.mark.django_db
class TestTokenModel:
    """Test Token model."""

    def test_token_str_representation(self):
        """Token string representation includes name and type."""
        token, _ = create_token(name="Test Token")

        assert str(token) == "Test Token (user)"

    def test_token_has_uuid_primary_key(self):
        """Token uses UUID as primary key."""
        token, _ = create_token(name="test-token")

        assert len(str(token.pk)) == 36  # UUID format

    def test_token_default_token_type(self):
        """Token defaults to USER type."""
        token, _ = create_token(name="test-token")

        assert token.token_type == Token.TokenType.USER

    def test_token_system_type(self):
        """Token can be created with SYSTEM type."""
        token, _ = create_token(name="system-token", token_type=Token.TokenType.SYSTEM)

        assert token.token_type == Token.TokenType.SYSTEM

    def test_token_is_expired_property_true(self):
        """is_expired returns True for expired token."""
        token, _ = create_token(name="expired-token", expires_at=timezone.now() - timedelta(days=1))

        assert token.is_expired is True

    def test_token_is_expired_property_false(self):
        """is_expired returns False for valid token."""
        token, _ = create_token(name="valid-token", expires_at=timezone.now() + timedelta(days=1))

        assert token.is_expired is False

    def test_token_is_expired_no_expiry(self):
        """is_expired returns False for token without expiry."""
        token, _ = create_token(name="no-expiry-token")
        token.expires_at = None
        token.save()

        assert token.is_expired is False

    def test_token_is_active_true(self):
        """is_active returns True for valid, non-revoked token."""
        token, _ = create_token(name="active-token")

        assert token.is_active is True

    def test_token_is_active_revoked(self):
        """is_active returns False for revoked token."""
        token, _ = create_token(name="revoked-token")
        revoke_token(token)
        token.refresh_from_db()

        assert token.is_active is False

    def test_token_is_active_purged(self):
        """is_active returns False for purged token."""
        token, _ = create_token(name="purged-token")
        revoke_token(token, purge=True)
        token.refresh_from_db()

        assert token.is_active is False

    def test_token_is_active_expired(self):
        """is_active returns False for expired token."""
        token, _ = create_token(name="expired-token", expires_at=timezone.now() - timedelta(days=1))

        assert token.is_active is False

    def test_token_can_authenticate_active(self):
        """can_authenticate returns True for active token."""
        token, _ = create_token(name="active-token")

        assert token.can_authenticate() is True

    def test_token_can_authenticate_inactive(self):
        """can_authenticate returns False for inactive token."""
        token, _ = create_token(name="inactive-token")
        revoke_token(token)
        token.refresh_from_db()

        assert token.can_authenticate() is False

    def test_token_mark_used_updates_timestamp(self):
        """mark_used updates last_used_at timestamp."""
        token, _ = create_token(name="test-token")
        assert token.last_used_at is None

        token.mark_used()

        assert token.last_used_at is not None

    def test_token_mark_used_without_commit(self):
        """mark_used with commit=False doesn't save to database."""
        token, _ = create_token(name="test-token")

        token.mark_used(commit=False)

        # Should be updated in memory
        assert token.last_used_at is not None

        # But not in database
        token.refresh_from_db()
        assert token.last_used_at is None

    def test_token_ordering(self):
        """Tokens are ordered by created_at descending."""
        token1, _ = create_token(name="older-token")
        token2, _ = create_token(name="newer-token")

        tokens = list(Token.objects.all())
        assert tokens[0].pk == token2.pk
        assert tokens[1].pk == token1.pk

    def test_token_unique_key_constraint(self):
        """Token key must be unique."""
        from django.db import IntegrityError

        token1, _ = create_token(name="token-1")

        with pytest.raises(IntegrityError):
            Token.objects.create(
                name="token-2",
                key=token1.key,
                prefix="tok_unique2",
                hint="hint2",
            )


@pytest.mark.django_db
class TestTokenAuditLogModel:
    """Test TokenAuditLog model."""

    def test_audit_log_str_representation(self):
        """Audit log string representation includes action and token."""
        token, _ = create_token(name="test-token")
        log = TokenAuditLog.objects.create(
            token=token,
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            path="/api/test/",
            method="GET",
            status_code=200,
        )

        assert "auth_success" in str(log)
        assert str(token.pk) in str(log)

    def test_audit_log_without_token(self):
        """Audit log can be created without token (for failed auth)."""
        log = TokenAuditLog.objects.create(
            action=TokenAuditLog.ACTION_AUTH_FAILED,
            path="/api/test/",
            method="GET",
            status_code=401,
        )

        assert log.token is None
        assert "unknown-token" in str(log)

    def test_audit_log_action_choices(self):
        """Audit log action must be one of the defined choices."""
        token, _ = create_token(name="test-token")

        valid_actions = [
            TokenAuditLog.ACTION_AUTH_SUCCESS,
            TokenAuditLog.ACTION_AUTH_FAILED,
            TokenAuditLog.ACTION_REVOKED,
            TokenAuditLog.ACTION_ROTATED,
        ]

        for action in valid_actions:
            log = TokenAuditLog(
                token=token,
                action=action,
                path="/api/test/",
                method="GET",
                status_code=200,
            )
            # Should not raise validation error
            log.full_clean()

    def test_audit_log_extra_json_field(self):
        """Audit log extra field stores JSON data."""
        token, _ = create_token(name="test-token")
        log = TokenAuditLog.objects.create(
            token=token,
            action=TokenAuditLog.ACTION_AUTH_FAILED,
            path="/api/test/",
            method="GET",
            status_code=401,
            extra={"error_code": "invalid_token", "ip": "127.0.0.1"},
        )

        assert log.extra["error_code"] == "invalid_token"
        assert log.extra["ip"] == "127.0.0.1"

    def test_audit_log_ordering(self):
        """Audit logs are ordered by created_at descending."""
        token, _ = create_token(name="test-token")

        log1 = TokenAuditLog.objects.create(
            token=token,
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            path="/api/test/",
            method="GET",
            status_code=200,
        )
        log2 = TokenAuditLog.objects.create(
            token=token,
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            path="/api/test/",
            method="GET",
            status_code=200,
        )

        logs = list(TokenAuditLog.objects.all())
        assert logs[0].pk == log2.pk
        assert logs[1].pk == log1.pk

    def test_audit_log_related_to_token(self):
        """Audit logs can be accessed from token via related_name."""
        token, _ = create_token(name="test-token")

        TokenAuditLog.objects.create(
            token=token,
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            path="/api/test/",
            method="GET",
            status_code=200,
        )

        assert token.audit_logs.count() == 1
