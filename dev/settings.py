import os
from importlib.util import find_spec
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HAS_DRF = find_spec("rest_framework") is not None

SECRET_KEY = "dev-only-not-for-production"
DEBUG = True
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "keysmith",
    "tokenlab",
]
if HAS_DRF:
    INSTALLED_APPS.append("rest_framework")

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "dev.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "dev.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} | {levelname:8} | {name} | {module}:{funcName}:{lineno} - {message}",
            "style": "{",
        },
        "colored": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {levelname} | {name} | {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "filters": ["require_debug_true"],
        },
        "file_info": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "info.log"),
            "formatter": "verbose",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "error.log"),
            "formatter": "verbose",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
            "include_html": True,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_info", "mail_admins"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["file_error", "mail_admins"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "shortener": {  # Replace with your app name or create loggers for each app
            "handlers": ["console", "file_info", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    # Root logger - catches anything missed by other loggers
    "root": {
        "handlers": ["console", "file_info", "file_error"],
        "level": "INFO",
    },
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"
STATIC_DIR = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [STATIC_DIR] if os.path.isdir(STATIC_DIR) else []
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

if HAS_DRF:
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "keysmith.drf.auth.KeysmithAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
    }
