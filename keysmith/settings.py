from django.conf import settings
from django.core.signals import setting_changed
from django.utils.translation import gettext_lazy as _

DEFAULT_TOKEN_MODEL = "keysmith.Token"  # nosec B105
DEFAULT_TOKEN_PREFIX = "tok"  # nosec B105
DEFAULT_TOKEN_SECRET_LENGTH = 32  # nosec B105

KEYSMITH_DEFAULTS = {
    "HASH_BACKEND": "keysmith.hashers.PBKDF2SHA512TokenHasher",
    "HASH_ITERATIONS": 100_000,
    "DEFAULT_EXPIRY_DAYS": 90,
    "AVAILABLE_SCOPES": [],
    "DEFAULT_SCOPES": [],
    "TOKEN_MODEL": DEFAULT_TOKEN_MODEL,
    "HEADER_NAME": "HTTP_X_KEYSMITH_TOKEN",
    "ALLOW_QUERY_PARAM": False,
    "QUERY_PARAM_NAME": "keysmith_token",
    "ENABLE_AUDIT_LOGGING": True,
    "AUDIT_LOG_MODEL": "keysmith.TokenAuditLog",
    "AUDIT_LOG_HOOK": None,
    "AUDIT_LOG_RETENTION_DAYS": None,
    "TRUST_PROXIES": False,
    "CLIENT_IP_HEADER": None,  # Optional header for client IP (e.g. "HTTP_X_REAL_IP", "HTTP_CF_CONNECTING_IP")
    "CLIENT_IP_HOOK": None,  # Optional callable or dotted string: hook(request) -> str | None
    "LAST_USED_UPDATE_INTERVAL": 60,  # Minimum seconds between last_used_at DB updates (0 = every request)
    "AUTH_HEADER_TYPES": ("Bearer", "Token"),  # Supported auth header schemes in Authorization header
    "WWW_AUTHENTICATE_SCHEME": "Bearer",  # Auth scheme in WWW-Authenticate header per RFC 9110
    "TOKEN_PREFIX": DEFAULT_TOKEN_PREFIX,
    "TOKEN_SECRET_LENGTH": DEFAULT_TOKEN_SECRET_LENGTH,
    "RATE_LIMIT_HOOK": None,  # Optional dotted callable: hook(request, raw_token=None)
    "DRF_THROTTLE_HOOK": None,  # Optional dotted callable: hook(request, token=None)
    "DEFAULT_ERROR_MESSAGES": {
        "missing_token": _("Authentication credentials were not provided."),
        "invalid_token": _("Your session has expired or the token is invalid."),
        "insufficient_scope": _("You do not have permission to perform this action."),
        "rate_limited": _("Too many authentication attempts. Try again later."),
    },
}


class KeysmithSettings:
    """Lazy proxy around the `KEYSMITH` Django setting."""

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

        if attr == "DEFAULT_ERROR_MESSAGES":
            default_messages = KEYSMITH_DEFAULTS[attr]
            user_messages = self.user_settings.get(attr, {})
            val = {**default_messages, **user_messages}
        else:
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
