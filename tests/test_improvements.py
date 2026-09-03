from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.http import HttpRequest
from django.test import RequestFactory
from django.utils import timezone

from keysmith.audit.logger import _get_ip_address, _is_valid_ip
from keysmith.auth.base import authenticate_token
from keysmith.drf.auth import KeysmithAuthentication
from keysmith.drf.throttling import KeysmithTokenRateThrottle
from keysmith.hashers.sha256 import HMACSHA256TokenHasher, SHA256TokenHasher
from keysmith.hooks import load_hook
from keysmith.models import Token
from keysmith.services.tokens import create_token, mark_token_used, rotate_token


class TestIPExtractionAndValidation:
    def test_is_valid_ip(self):
        assert _is_valid_ip("127.0.0.1") is True
        assert _is_valid_ip("::1") is True
        assert _is_valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert _is_valid_ip("not-an-ip") is False
        assert _is_valid_ip("") is False
        assert _is_valid_ip(None) is False
        assert _is_valid_ip("1.2.3.4.5") is False

    def test_client_ip_hook_precedence(self, settings):
        settings.KEYSMITH = {
            **settings.KEYSMITH,
            "CLIENT_IP_HOOK": lambda req: "198.51.100.42",
        }
        req = HttpRequest()
        req.META = {"REMOTE_ADDR": "127.0.0.1"}
        assert _get_ip_address(req) == "198.51.100.42"

    def test_client_ip_header(self, settings):
        settings.KEYSMITH = {
            **settings.KEYSMITH,
            "CLIENT_IP_HEADER": "HTTP_CF_CONNECTING_IP",
        }
        req = HttpRequest()
        req.META = {
            "HTTP_CF_CONNECTING_IP": "203.0.113.195",
            "REMOTE_ADDR": "127.0.0.1",
        }
        assert _get_ip_address(req) == "203.0.113.195"

    def test_client_ip_header_ignores_invalid_ip(self, settings):
        settings.KEYSMITH = {
            **settings.KEYSMITH,
            "CLIENT_IP_HEADER": "HTTP_X_REAL_IP",
        }
        req = HttpRequest()
        req.META = {
            "HTTP_X_REAL_IP": "malicious<script>",
            "REMOTE_ADDR": "127.0.0.1",
        }
        assert _get_ip_address(req) == "127.0.0.1"


class TestFastHashers:
    def test_sha256_hasher(self):
        hasher = SHA256TokenHasher()
        secret = "secret-123456789012345678901234"
        hashed = hasher.hash(secret)
        assert hashed.startswith("sha256$")
        assert hasher.verify(secret, hashed) is True
        assert hasher.verify("wrong-secret", hashed) is False

    def test_hmac_sha256_hasher(self):
        hasher = HMACSHA256TokenHasher()
        secret = "secret-123456789012345678901234"
        hashed = hasher.hash(secret)
        assert hashed.startswith("hmac_sha256$")
        assert hasher.verify(secret, hashed) is True
        assert hasher.verify("wrong-secret", hashed) is False


class TestCallableHooks:
    def test_load_hook_with_callable(self, settings):
        def my_hook(req, token=None):
            return "hook-called"

        settings.KEYSMITH = {
            **settings.KEYSMITH,
            "DRF_THROTTLE_HOOK": my_hook,
        }
        hook = load_hook("DRF_THROTTLE_HOOK")
        assert hook is my_hook
        assert hook(None) == "hook-called"


@pytest.mark.django_db
class TestDebouncedLastUsedAt:
    def test_mark_token_used_debouncing(self, settings):
        settings.KEYSMITH = {
            **settings.KEYSMITH,
            "LAST_USED_UPDATE_INTERVAL": 60,
        }
        token, _ = create_token(name="debounce-token")
        mark_token_used(token)
        initial_time = token.last_used_at
        assert initial_time is not None

        # Immediate second call within interval should not change DB timestamp
        with patch.object(Token.objects, "filter") as mock_filter:
            mark_token_used(token)
            mock_filter.assert_not_called()

    def test_mark_token_used_updates_in_memory(self):
        token, raw = create_token(name="in-memory-token")
        assert token.last_used_at is None
        auth_token = authenticate_token(raw)
        assert auth_token.last_used_at is not None


@pytest.mark.django_db
class TestAuthHeaders:
    def test_bearer_header_in_middleware(self, client):
        _, raw = create_token(name="bearer-token")
        response = client.get("/api/status/", HTTP_AUTHORIZATION=f"Bearer {raw}")
        assert response.status_code == 200
        assert response.json()["authenticated"] is True

    def test_token_scheme_header_in_middleware(self, client):
        _, raw = create_token(name="token-scheme")
        response = client.get("/api/status/", HTTP_AUTHORIZATION=f"Token {raw}")
        assert response.status_code == 200
        assert response.json()["authenticated"] is True

    def test_drf_authenticate_header_rfc_compliant(self):
        auth = KeysmithAuthentication()
        req = RequestFactory().get("/")
        header = auth.authenticate_header(req)
        assert "Bearer" in header
        assert "realm=" in header

    def test_drf_bearer_header_authentication(self, client):
        _, raw = create_token(name="drf-bearer")
        response = client.get("/api/drf/status/", HTTP_AUTHORIZATION=f"Bearer {raw}")
        assert response.status_code == 200
        assert response.json()["authenticated"] is True


@pytest.mark.django_db
class TestRotateTokenExpiresAt:
    def test_rotate_expired_token_resets_expiry(self):
        expired_time = timezone.now() - timedelta(days=5)
        token, _ = create_token(name="expired-rot", expires_at=expired_time)
        assert token.is_expired is True

        new_raw = rotate_token(token)
        token.refresh_from_db()
        assert token.is_expired is False
        assert token.expires_at > timezone.now()

        # Should authenticate successfully
        authenticated = authenticate_token(new_raw)
        assert authenticated.pk == token.pk


@pytest.mark.django_db
class TestManagementCommands:
    def test_create_token_command(self):
        out = StringIO()
        call_command("create_token", name="cli-token", stdout=out)
        output = out.getvalue()
        assert "Successfully created token" in output
        assert "tok_" in output
        assert Token.objects.filter(name="cli-token").exists()

    def test_revoke_token_command(self):
        token, _ = create_token(name="cli-revoke")
        out = StringIO()
        call_command("revoke_token", token.prefix, stdout=out)
        token.refresh_from_db()
        assert token.revoked is True
        assert "Successfully revoked" in out.getvalue()

    def test_list_tokens_command(self):
        token, _ = create_token(name="cli-list")
        out = StringIO()
        call_command("list_tokens", active=True, stdout=out)
        output = out.getvalue()
        assert token.prefix in output
        assert "Active" in output


class TestThrottleClass:
    def test_throttle_cache_key_with_token(self):
        throttle = KeysmithTokenRateThrottle()
        req = RequestFactory().get("/")
        token = Token(prefix="tok_test123")
        req.auth = token
        key = throttle.get_cache_key(req, None)
        assert key is not None
        assert "tok_test123" in key
