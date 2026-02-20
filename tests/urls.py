from importlib.util import find_spec

from django.contrib import admin
from django.urls import include, path

from tests import views

HAS_DRF = find_spec("rest_framework") is not None

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/status/", views.token_status_view, name="token_status"),
    path("api/resources/", views.resource_collection_view, name="resource_collection"),
    path("api/resources/<int:pk>/", views.resource_detail_view, name="resource_detail"),
]

if HAS_DRF:
    urlpatterns.append(path("api/drf/", include("tests.drf_urls")))
