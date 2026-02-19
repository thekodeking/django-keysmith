import pytest

from keysmith.services.tokens import create_token, revoke_token

drf_only = pytest.mark.skipif(
    not pytest.importorskip("rest_framework", reason="DRF not installed"),
    reason="DRF not installed",
)


@drf_only
@pytest.mark.django_db
class TestDRFAuthentication:
    """Test DRF authentication classes."""

    def test_drf_authentication_success(self, client):
        """DRF authenticates valid token successfully."""
        token, raw_token = create_token(name="test-token")

        response = client.get(
            "/api/drf/status/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200
        assert response.json()["authenticated"] is True
        assert response.json()["token_prefix"] == token.prefix

    def test_drf_authentication_missing_token(self, client):
        """DRF returns 401 when token is missing."""
        response = client.get("/api/drf/status/")

        assert response.status_code == 401

    def test_drf_authentication_invalid_token(self, client):
        """DRF returns 401 when token is invalid."""
        response = client.get(
            "/api/drf/status/",
            HTTP_X_KEYSMITH_TOKEN="invalid-token",
        )

        assert response.status_code == 401

    def test_drf_authentication_revoked_token(self, client):
        """DRF returns 401 when token is revoked."""
        token, raw_token = create_token(name="revoked-token")
        revoke_token(token)

        response = client.get(
            "/api/drf/status/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 401

    def test_drf_sets_auth_attribute(self, client):
        """DRF sets request.auth to the token object."""
        token, raw_token = create_token(name="test-token")

        response = client.get(
            "/api/drf/status/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200
        assert response.json()["token_prefix"] is not None


@drf_only
@pytest.mark.django_db
class TestDRFPermissionClasses:
    """Test DRF permission classes."""

    def test_require_keysmith_token_allows_authenticated(self, client):
        """RequireKeysmithToken allows authenticated requests."""
        _, raw_token = create_token(name="test-token")

        response = client.get(
            "/api/drf/status/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200

    def test_require_keysmith_token_rejects_unauthenticated(self, client):
        """RequireKeysmithToken rejects unauthenticated requests."""
        response = client.get("/api/drf/status/")

        assert response.status_code == 401

    def test_has_keysmith_scopes_allows_with_scope(self, client, django_db_blocker):
        """HasKeysmithScopes allows access when token has required scope."""
        from django.contrib.auth.models import Permission

        with django_db_blocker.unblock():
            permission = Permission.objects.create(
                codename="write",
                name="Can write",
                content_type_id=1,
            )

        token, raw_token = create_token(name="scoped-token", scopes=[permission])

        response = client.get(
            "/api/drf/scoped/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200
        assert response.json()["scoped"] is True

    def test_has_keysmith_scopes_rejects_without_scope(self, client):
        """HasKeysmithScopes rejects access when token lacks required scope."""
        _, raw_token = create_token(name="unscoped-token")

        response = client.get(
            "/api/drf/scoped/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 403


@drf_only
@pytest.mark.django_db
class TestDRFResourceViews:
    """Integration tests for DRF resource views."""

    def test_drf_resource_collection_get(self, client):
        """GET /api/drf/resources/ returns list of resources."""
        _, raw_token = create_token(name="test-token")

        response = client.get(
            "/api/drf/resources/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200
        assert "items" in response.json()

    def test_drf_resource_collection_post(self, client):
        """POST /api/drf/resources/ creates a new resource."""
        _, raw_token = create_token(name="test-token")

        response = client.post(
            "/api/drf/resources/",
            data={"name": "Test Resource", "description": "Test"},
            content_type="application/json",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 201
        assert response.json()["name"] == "Test Resource"

    def test_drf_resource_detail_get(self, client):
        """GET /api/drf/resources/<pk>/ returns resource details."""
        from tests.models import TestResource

        resource = TestResource.objects.create(name="Test Resource")
        _, raw_token = create_token(name="test-token")

        response = client.get(
            f"/api/drf/resources/{resource.pk}/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200
        assert response.json()["id"] == resource.pk

    def test_drf_resource_detail_put(self, client):
        """PUT /api/drf/resources/<pk>/ updates resource."""
        from tests.models import TestResource

        resource = TestResource.objects.create(name="Old Name")
        _, raw_token = create_token(name="test-token")

        response = client.put(
            f"/api/drf/resources/{resource.pk}/",
            data={"name": "New Name", "description": "Updated"},
            content_type="application/json",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_drf_resource_detail_patch(self, client):
        """PATCH /api/drf/resources/<pk>/ partially updates resource."""
        from tests.models import TestResource

        resource = TestResource.objects.create(name="Original", description="Desc")
        _, raw_token = create_token(name="test-token")

        response = client.patch(
            f"/api/drf/resources/{resource.pk}/",
            data={"name": "Updated"},
            content_type="application/json",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated"
        assert response.json()["description"] == "Desc"  # Unchanged

    def test_drf_resource_detail_delete(self, client):
        """DELETE /api/drf/resources/<pk>/ deletes resource."""
        from tests.models import TestResource

        resource = TestResource.objects.create(name="To Delete")
        _, raw_token = create_token(name="test-token")

        response = client.delete(
            f"/api/drf/resources/{resource.pk}/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 204
        assert not TestResource.objects.filter(pk=resource.pk).exists()

    def test_drf_resource_not_found(self, client):
        """Accessing non-existent resource returns 404."""
        _, raw_token = create_token(name="test-token")

        response = client.get(
            "/api/drf/resources/99999/",
            HTTP_X_KEYSMITH_TOKEN=raw_token,
        )

        assert response.status_code == 404
