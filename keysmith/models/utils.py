from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from keysmith.settings import keysmith_settings


def get_token_model():
    try:
        return apps.get_model(keysmith_settings.TOKEN_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "TOKEN_MODEL must be of the form 'app_label.ModelName'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"Token model '{keysmith_settings.TOKEN_MODEL}' not found"
        )


def get_audit_log_model():
    try:
        return apps.get_model(keysmith_settings.AUDIT_LOG_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "AUDIT_LOG_MODEL must be of the form 'app_label.ModelName'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"Audit log model '{keysmith_settings.AUDIT_LOG_MODEL}' not found"
        )
