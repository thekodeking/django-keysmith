from django.apps import AppConfig


class KeysmithConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "keysmith"

    def ready(self):
        import keysmith.checks  # noqa: F401
