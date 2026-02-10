from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("token-check/drf/", include("tokenlab.urls")),
    path("token-check/plain/", include("tokenlab.plain_urls")),
]
