from keysmith.settings import keysmith_settings


def get_message(key: str, *, default: str | None = None) -> str:
    return keysmith_settings.DEFAULT_ERROR_MESSAGES.get(key, default or key)
