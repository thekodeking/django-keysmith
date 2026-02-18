"""Django app configuration for tests."""

from django.apps import AppConfig


class TestsConfig(AppConfig):
    """Test app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests"
    verbose_name = "Keysmith Tests"
