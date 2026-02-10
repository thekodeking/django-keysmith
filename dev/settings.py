from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "dev-only-not-for-production"
DEBUG = True
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "keysmith",
]

MIDDLEWARE: list[str] = []
ROOT_URLCONF = "dev.urls"
TEMPLATES: list[dict] = []
WSGI_APPLICATION = "dev.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
