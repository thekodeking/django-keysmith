import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "keysmith-tests-only-not-for-production"
DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"
ROOT_URLCONF = "tests.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "keysmith",
    "tests",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

LANGUAGE_CODE = "en-us"
USE_I18N = True

STATIC_URL = "/static/"

KEYSMITH = {
    "HASH_BACKEND": "keysmith.hashers.PBKDF2SHA512TokenHasher",
    "HASH_ITERATIONS": 100_000,
    "DEFAULT_EXPIRY_DAYS": 90,
    "ENABLE_AUDIT_LOGGING": True,
    "TOKEN_PREFIX": "tok",
    "TOKEN_SECRET_LENGTH": 32,
}

if importlib.util.find_spec("rest_framework") is not None:
    INSTALLED_APPS.append("rest_framework")
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "keysmith.drf.auth.KeysmithAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
    }
