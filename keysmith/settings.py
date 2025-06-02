from django.conf import settings
from django.core.signals import setting_changed

# TODO: to plan out configuration for the package
KEYSMITH_DEFAULTS = {
    # ─────────────────────────────────────────────────────────────
    # Token storage & hashing
    # ─────────────────────────────────────────────────────────────
    "HASH_BACKEND": "keysmith.hashers.PBKDF2SHA512TokenHasher",
    "HASH_ITERATIONS": 100_000,
    "SALT_LENGTH": 16,
    # ─────────────────────────────────────────────────────────────
    # Expiry
    # ─────────────────────────────────────────────────────────────
    "DEFAULT_EXPIRY_DAYS": 90,
    "ROTATE_ON_USE": False,     # If True, tokens automatically rotate (re-hash) on each use
    # ─────────────────────────────────────────────────────────────
    # Scopes & Permissions
    # ─────────────────────────────────────────────────────────────
    # Allowed “scope” names (must map to your DRF permissions logic)
    "AVAILABLE_SCOPES": [
        "read",
        "write",
        "admin",
        "audit",
    ],
    "DEFAULT_SCOPES": ["read"],
    "PERMISSION_CLASS": "rest_framework.permissions.BasePermission",     # DRF Permission class to enforce scopes (must implement `.has_permission`)
    # ─────────────────────────────────────────────────────────────
    # Token modeling
    # ─────────────────────────────────────────────────────────────
    "TOKEN_MODEL": "keysmith.models.Token",
    # ─────────────────────────────────────────────────────────────
    # Transmission & retrieval
    # ─────────────────────────────────────────────────────────────
    # Header name where clients send their token
    "HEADER_NAME": "HTTP_X_KEYSMITH_TOKEN",
    # Query-param fallback (e.g. ?token=…)
    "ALLOW_QUERY_PARAM": False,
    "QUERY_PARAM_NAME": "keysmith_token",
    # ─────────────────────────────────────────────────────────────
    # Auditing & logging
    # ─────────────────────────────────────────────────────────────
    "ENABLE_AUDIT_LOGGING": True,
    "AUDIT_LOG_MODEL": "keysmith.models.TokenAuthLog",
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
