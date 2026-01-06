from django.conf import settings
from django.core.signals import setting_changed

KEYSMITH_DEFAULTS = {
    "HASH_BACKEND": "keysmith.hashers.PBKDF2SHA512TokenHasher",
    "HASH_ITERATIONS": 100_000,
    "SALT_LENGTH": 16,
    "DEFAULT_EXPIRY_DAYS": 90,
    "ROTATE_ON_USE": False,  # If True, tokens automatically rotate (re-hash) on each use
    "AVAILABLE_SCOPES": [
        "read",
        "write",
        "admin",
        "audit",
    ],
    "DEFAULT_SCOPES": ["read"],
    "PERMISSION_CLASS": "rest_framework.permissions.BasePermission",  # DRF Permission class to enforce scopes (must implement `.has_permission`)
    "TOKEN_MODEL": "keysmith.models.Token",
    "HEADER_NAME": "HTTP_X_KEYSMITH_TOKEN",
    "ALLOW_QUERY_PARAM": False,
    "QUERY_PARAM_NAME": "keysmith_token",
    "ENABLE_AUDIT_LOGGING": True,
    "AUDIT_LOG_MODEL": "keysmith.models.TokenAuthLog",
    "TOKEN_PREFIX": "tok_",
    "TOKEN_LENGTH": 32,  # Length of the random value (excluding prefix and CRC)
    "TOKEN_MIN_LENGTH": 16,  # Minimum allowed token length
    "TOKEN_MAX_LENGTH": 64,  # Maximum allowed token length
    "CRC_DIGITS": 6,  # Number of digits in CRC checksum
    "HINT_LENGTH": 8,  # Number of characters to show as hint (last N chars)
}


class KeysmithSettings:
    def __init__(self, user_settings=None):
        if user_settings is not None:
            self._user_settings = user_settings
        self._cached_attrs = set()

    @property
    def user_settings(self):
        return getattr(settings, "KEYSMITH", {})

    def __getattr__(self, attr):
        if attr not in KEYSMITH_DEFAULTS:
            raise AttributeError(f"Invalid Keysmith setting: {attr!r}")

        val = self.user_settings.get(attr, KEYSMITH_DEFAULTS[attr])

        setattr(self, attr, val)
        self._cached_attrs.add(attr)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            del self._user_settings


keysmith_settings = KeysmithSettings()


def _reload_keysmith_settings(*, setting, **kwargs):
    if setting == "KEYSMITH":
        keysmith_settings.reload()


setting_changed.connect(_reload_keysmith_settings)
