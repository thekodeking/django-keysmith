"""Tests for Keysmith Django integration."""

import json

import pytest
from django.http import HttpRequest, JsonResponse
from django.test import Client, RequestFactory

from keysmith.django.decorator import keysmith_required
from keysmith.django.middleware import KeysmithAuthenticationMiddleware
from keysmith.django.permissions import keysmith_scopes
from keysmith.services.tokens import create_token, revoke_token


@pytest.mark.django_db
class TestKeysmithMiddleware:
    """Test Keysmith authentication middleware."""

    def test_middleware_sets_token_on_request(self):
        """Middleware populates keysmith_token on request."""
        token, raw_token = create_token(name="test-token")

        factory = RequestFactory()
        request = factory.get("/test/", HTTP_X_KEYSMITH_TOKEN=raw_token)

        def get_response(request):
            return JsonResponse({"ok": True})

        middleware = KeysmithAuthenticationMiddleware(get_response)
        middleware(request)

        assert request.keysmith_token is not None
        assert request.keysmith_token.pk == token.pk

    def test_middleware_sets_user_on_request(self):
        """Middleware populates keysmith_user on request."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.get("/test/", HTTP_X_KEYSMITH_TOKEN=raw_token)

        def get_response(request):
            return JsonResponse({"ok": True})

        middleware = KeysmithAuthenticationMiddleware(get_response)
        middleware(request)

        assert request.keysmith_user is not None
        assert request.keysmith_user.pk == user.pk

    def test_middleware_sets_none_for_missing_token(self):
        """Middleware sets None when token is not provided."""
        factory = RequestFactory()
        request = factory.get("/test/")

        def get_response(request):
            return JsonResponse({"ok": True})

        middleware = KeysmithAuthenticationMiddleware(get_response)
        middleware(request)

        assert request.keysmith_token is None
        assert request.keysmith_user is None

    def test_middleware_sets_auth_error_for_invalid_token(self):
        """Middleware sets auth_error when token is invalid."""
        factory = RequestFactory()
        request = factory.get("/test/", HTTP_X_KEYSMITH_TOKEN="invalid-token")

        def get_response(request):
            return JsonResponse({"ok": True})

        middleware = KeysmithAuthenticationMiddleware(get_response)
        middleware(request)

        assert request.keysmith_token is None
        assert request.keysmith_auth_error is not None


@pytest.mark.django_db
class TestKeysmithDecorator:
    """Test @keysmith_required decorator."""

    def test_decorator_allows_authenticated_request(self):
        """Decorator allows requests with valid authentication."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        @keysmith_required
        def test_view(request):
            return JsonResponse({"authenticated": True})

        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.get("/test/", HTTP_X_KEYSMITH_TOKEN=raw_token)

        # Simulate middleware processing
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
        except Exception as e:
            request.keysmith_auth_error = e

        response = test_view(request)

        assert response.status_code == 200

    def test_decorator_rejects_missing_token(self):
        """Decorator rejects requests without token."""

        @keysmith_required
        def test_view(request):
            return JsonResponse({"authenticated": True})

        factory = RequestFactory()
        request = factory.get("/test/")
        request.keysmith_user = None
        request.keysmith_token = None
        request.keysmith_auth_error = None

        response = test_view(request)

        assert response.status_code == 401

    def test_decorator_rejects_invalid_token(self):
        """Decorator rejects requests with invalid token."""
        from keysmith.auth.exceptions import InvalidToken

        @keysmith_required
        def test_view(request):
            return JsonResponse({"authenticated": True})

        factory = RequestFactory()
        request = factory.get("/test/")
        request.keysmith_user = None
        request.keysmith_token = None
        request.keysmith_auth_error = InvalidToken("Invalid")

        response = test_view(request)

        assert response.status_code == 401

    def test_decorator_rejects_revoked_token(self):
        """Decorator rejects requests with revoked token."""
        from keysmith.auth.exceptions import RevokedToken

        @keysmith_required
        def test_view(request):
            return JsonResponse({"authenticated": True})

        factory = RequestFactory()
        request = factory.get("/test/")
        request.keysmith_user = None
        request.keysmith_token = None
        request.keysmith_auth_error = RevokedToken("Revoked")

        response = test_view(request)

        assert response.status_code == 401


@pytest.mark.django_db
class TestKeysmithScopesDecorator:
    """Test @keysmith_scopes decorator."""

    def test_scope_decorator_allows_with_required_scope(self, django_db_blocker):
        """Scope decorator allows access when token has required scope."""
        from django.contrib.auth.models import Permission
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        @keysmith_required
        @keysmith_scopes("write")
        def test_view(request):
            return JsonResponse({"scoped": True})

        with django_db_blocker.unblock():
            permission = Permission.objects.create(
                codename="write",
                name="Can write",
                content_type_id=1,
            )

        token, _ = create_token(name="scoped-token", user=user, scopes=[permission])

        factory = RequestFactory()
        request = factory.get("/test/")
        request.keysmith_token = token
        request.keysmith_user = user
        request.keysmith_auth_error = None

        response = test_view(request)

        assert response.status_code == 200

    def test_scope_decorator_custom_message(self):
        """Scope decorator can use custom missing token message."""

        @keysmith_required(missing_message="Custom missing message")
        def view(request):
            return JsonResponse({"ok": True})

        factory = RequestFactory()
        request = factory.get("/test/")
        request.keysmith_user = None
        request.keysmith_token = None
        request.keysmith_auth_error = None

        response = view(request)
        assert response.status_code == 401

    def test_allow_anonymous_parameter(self):
        """Decorator can allow anonymous access."""

        @keysmith_required(allow_anonymous=True)
        def view(request):
            return JsonResponse({"ok": True})

        factory = RequestFactory()
        request = factory.get("/test/")
        request.keysmith_user = None
        request.keysmith_token = None
        request.keysmith_auth_error = None

        response = view(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestPlainDjangoViews:
    """Integration tests for plain Django views."""

    def test_resource_collection_get(self):
        """GET /api/resources/ returns list of resources."""
        from tests.models import TestResource
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.get("/api/resources/", HTTP_X_KEYSMITH_TOKEN=raw_token)

        # Simulate middleware
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
            request.keysmith_auth_error = None
        except Exception as e:
            request.keysmith_auth_error = e

        from tests.views import resource_collection_view

        response = resource_collection_view(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert "items" in data

    def test_resource_collection_post_creates_resource(self):
        """POST /api/resources/ creates a new resource."""
        from tests.models import TestResource
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.post(
            "/api/resources/",
            data=json.dumps({"name": "Test Resource", "description": "Test"}),
            content_type="application/json",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        # Simulate middleware
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
            request.keysmith_auth_error = None
        except Exception as e:
            request.keysmith_auth_error = e

        from tests.views import resource_collection_view

        response = resource_collection_view(request)

        assert response.status_code == 201
        data = json.loads(response.content)
        assert data["name"] == "Test Resource"

    def test_resource_collection_post_requires_name(self):
        """POST /api/resources/ requires name field."""
        from tests.models import TestResource
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.post(
            "/api/resources/",
            data=json.dumps({"description": "Test"}),
            content_type="application/json",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        # Simulate middleware
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
            request.keysmith_auth_error = None
        except Exception as e:
            request.keysmith_auth_error = e

        from tests.views import resource_collection_view

        response = resource_collection_view(request)

        assert response.status_code == 400

    def test_resource_detail_get(self):
        """GET /api/resources/<pk>/ returns resource details."""
        from tests.models import TestResource
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        resource = TestResource.objects.create(name="Test Resource")
        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.get(f"/api/resources/{resource.pk}/", HTTP_X_KEYSMITH_TOKEN=raw_token)

        # Simulate middleware
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
            request.keysmith_auth_error = None
        except Exception as e:
            request.keysmith_auth_error = e

        from tests.views import resource_detail_view

        response = resource_detail_view(request, pk=resource.pk)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["id"] == resource.pk

    def test_resource_detail_put_updates(self):
        """PUT /api/resources/<pk>/ updates resource."""
        from tests.models import TestResource
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        resource = TestResource.objects.create(name="Old Name")
        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.put(
            f"/api/resources/{resource.pk}/",
            data=json.dumps({"name": "New Name", "description": "Updated"}),
            content_type="application/json",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        # Simulate middleware
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
            request.keysmith_auth_error = None
        except Exception as e:
            request.keysmith_auth_error = e

        from tests.views import resource_detail_view

        response = resource_detail_view(request, pk=resource.pk)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["name"] == "New Name"

    def test_resource_detail_delete(self):
        """DELETE /api/resources/<pk>/ deletes resource."""
        from tests.models import TestResource
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        resource = TestResource.objects.create(name="To Delete")
        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.delete(f"/api/resources/{resource.pk}/", HTTP_X_KEYSMITH_TOKEN=raw_token)

        # Simulate middleware
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
            request.keysmith_auth_error = None
        except Exception as e:
            request.keysmith_auth_error = e

        from tests.views import resource_detail_view

        response = resource_detail_view(request, pk=resource.pk)

        assert response.status_code == 204
        assert not TestResource.objects.filter(pk=resource.pk).exists()

    def test_resource_detail_not_found(self):
        """Accessing non-existent resource returns 404."""
        from tests.models import TestResource
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="testuser")

        token, raw_token = create_token(name="test-token", user=user)

        factory = RequestFactory()
        request = factory.get("/api/resources/99999/", HTTP_X_KEYSMITH_TOKEN=raw_token)

        # Simulate middleware
        from keysmith.auth.base import authenticate_token

        try:
            auth_token = authenticate_token(raw_token)
            request.keysmith_token = auth_token
            request.keysmith_user = auth_token.user
            request.keysmith_auth_error = None
        except Exception as e:
            request.keysmith_auth_error = e

        from tests.views import resource_detail_view

        response = resource_detail_view(request, pk=99999)

        assert response.status_code == 404
