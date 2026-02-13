from importlib.util import find_spec

from django.contrib import admin
from django.urls import include, path

HAS_DRF = find_spec("rest_framework") is not None

urlpatterns = [
    path("admin/", admin.site.urls),
    path("token-check/plain/", include("tokenlab.plain_urls")),
]

if HAS_DRF:
    urlpatterns.append(path("token-check/drf/", include("tokenlab.urls")))
