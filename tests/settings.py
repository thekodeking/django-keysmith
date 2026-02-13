"""Minimal Django settings used for Keysmith automated tests."""

SECRET_KEY = "keysmith-tests-only"
DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"
ROOT_URLCONF = "tests.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "keysmith",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
