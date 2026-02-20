from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from keysmith.settings import keysmith_settings


def get_token_model():
    """Return the configured token model class."""
    try:
        return apps.get_model(keysmith_settings.TOKEN_MODEL)
    except ValueError as exc:
        raise ImproperlyConfigured("TOKEN_MODEL must be of the form 'app_label.ModelName'") from exc
    except LookupError as exc:
        raise ImproperlyConfigured(
            f"Token model '{keysmith_settings.TOKEN_MODEL}' not found"
        ) from exc


def get_audit_log_model():
    """Return the configured audit log model class."""
    try:
        return apps.get_model(keysmith_settings.AUDIT_LOG_MODEL)
    except ValueError as exc:
        raise ImproperlyConfigured(
            "AUDIT_LOG_MODEL must be of the form 'app_label.ModelName'"
        ) from exc
    except LookupError as exc:
        raise ImproperlyConfigured(
            f"Audit log model '{keysmith_settings.AUDIT_LOG_MODEL}' not found"
        ) from exc
