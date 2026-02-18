"""DRF URL configuration for Keysmith test suite."""

from django.urls import path

from tests import drf_views

urlpatterns = [
    path("status/", drf_views.TokenStatusAPIView.as_view(), name="drf_token_status"),
    path(
        "resources/", drf_views.ResourceCollectionAPIView.as_view(), name="drf_resource_collection"
    ),
    path(
        "resources/<int:pk>/", drf_views.ResourceDetailAPIView.as_view(), name="drf_resource_detail"
    ),
    path("scoped/", drf_views.ScopedResourceAPIView.as_view(), name="drf_scoped_resource"),
]
