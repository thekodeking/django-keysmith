from unittest.mock import patch

import pytest
from django.http import HttpRequest

from keysmith.audit.logger import _get_ip_address, _request_context, log_audit_event
from keysmith.models import TokenAuditLog
from keysmith.services.tokens import create_token, purge_token, revoke_token, rotate_token


@pytest.mark.django_db
class TestAuditLogging:
    """Test audit logging functionality."""

    def test_audit_log_created_on_token_create_via_service(self):
        """Audit logs can be created for token lifecycle events."""
        token, _ = create_token(name="test-token")

        log_audit_event(
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            token=token,
            status_code=200,
        )

        assert TokenAuditLog.objects.filter(token=token).exists()

    def test_audit_log_created_on_revoke(self):
        """Revoking a token creates audit log."""
        token, _ = create_token(name="test-token")

        revoke_token(token)

        log = TokenAuditLog.objects.filter(token=token, action=TokenAuditLog.ACTION_REVOKED).first()
        assert log is not None

    def test_audit_log_created_on_purge(self):
        """Purging a token creates audit log with purge marker."""
        token, _ = create_token(name="test-token")

        purge_token(token)

        log = TokenAuditLog.objects.filter(token=token, action=TokenAuditLog.ACTION_REVOKED).first()
        assert log is not None
        assert log.extra.get("purge") is True

    def test_audit_log_created_on_rotate(self):
        """Rotating a token creates audit log."""
        token, _ = create_token(name="test-token")

        rotate_token(token)

        log = TokenAuditLog.objects.filter(token=token, action=TokenAuditLog.ACTION_ROTATED).first()
        assert log is not None

    def test_audit_log_without_request(self):
        """Audit log can be created without request object."""
        token, _ = create_token(name="test-token")

        log_audit_event(
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            token=token,
            status_code=200,
        )

        log = TokenAuditLog.objects.first()
        assert log.path == ""
        assert log.method == ""

    def test_audit_log_with_request_context(self):
        """Audit log captures request context."""
        request = HttpRequest()
        request.method = "POST"
        request.path = "/api/test/"
        request.META = {
            "REMOTE_ADDR": "192.168.1.1",
            "HTTP_USER_AGENT": "TestAgent/1.0",
        }

        token, _ = create_token(name="test-token")

        log_audit_event(
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            request=request,
            token=token,
            status_code=200,
        )

        log = TokenAuditLog.objects.first()
        assert log.path == "/api/test/"
        assert log.method == "POST"
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "TestAgent/1.0"

    def test_audit_log_with_extra_data(self):
        """Audit log can include extra data."""
        token, _ = create_token(name="test-token")

        log_audit_event(
            action=TokenAuditLog.ACTION_AUTH_FAILED,
            token=token,
            status_code=401,
            extra={"error_code": "invalid_token", "reason": "expired"},
        )

        log = TokenAuditLog.objects.first()
        assert log.extra["error_code"] == "invalid_token"
        assert log.extra["reason"] == "expired"

    def test_audit_log_disabled_by_settings(self, settings):
        """Audit logging can be disabled via settings."""
        settings.KEYSMITH = {
            **settings.KEYSMITH,
            "ENABLE_AUDIT_LOGGING": False,
        }

        token, _ = create_token(name="test-token")

        log_audit_event(
            action=TokenAuditLog.ACTION_AUTH_SUCCESS,
            token=token,
            status_code=200,
        )

        assert TokenAuditLog.objects.count() == 0

    def test_audit_log_swallows_exceptions(self):
        """Audit logging failures don't raise exceptions."""
        with patch("keysmith.audit.logger.get_audit_log_model") as mock_get:
            mock_get.side_effect = Exception("Database error")

            # Should not raise
            log_audit_event(
                action=TokenAuditLog.ACTION_AUTH_SUCCESS,
                status_code=200,
            )


class TestRequestContext:
    """Test request context extraction."""

    def test_request_context_extracts_basic_info(self):
        """Context extracts basic request info."""
        request = HttpRequest()
        request.method = "GET"
        request.path = "/api/test/"
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        context = _request_context(request, 200)

        assert context["path"] == "/api/test/"
        assert context["method"] == "GET"
        assert context["status_code"] == 200
        assert context["ip_address"] == "127.0.0.1"

    def test_request_context_extracts_user_agent(self):
        """Context extracts user agent."""
        request = HttpRequest()
        request.method = "GET"
        request.path = "/"
        request.META = {"HTTP_USER_AGENT": "Mozilla/5.0"}

        context = _request_context(request, 200)

        assert context["user_agent"] == "Mozilla/5.0"

    def test_get_ip_address_from_remote_addr(self):
        """IP address extracted from REMOTE_ADDR."""
        request = HttpRequest()
        request.META = {"REMOTE_ADDR": "192.168.1.1"}

        ip = _get_ip_address(request)

        assert ip == "192.168.1.1"

    def test_get_ip_address_from_x_forwarded_for(self):
        """IP address extracted from X-Forwarded-For header."""
        request = HttpRequest()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1",
            "REMOTE_ADDR": "192.168.1.1",
        }

        ip = _get_ip_address(request)

        assert ip == "10.0.0.1"

    def test_get_ip_address_none_when_missing(self):
        """IP address is None when not available."""
        request = HttpRequest()
        request.META = {}

        ip = _get_ip_address(request)

        assert ip is None

    def test_get_ip_address_handles_empty_x_forwarded_for(self):
        """IP address falls back to REMOTE_ADDR when X-Forwarded-For is empty."""
        request = HttpRequest()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "",
            "REMOTE_ADDR": "192.168.1.1",
        }

        ip = _get_ip_address(request)

        assert ip == "192.168.1.1"
