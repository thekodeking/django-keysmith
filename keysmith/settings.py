from django.conf import settings
from django.core.signals import setting_changed


# TODO: to plan out configuration for the package
KEYSMITH_DEFAULTS = {
    # ─────────────────────────────────────────────────────────────
    # Token storage & hashing
    # ─────────────────────────────────────────────────────────────
    # Which hash algorithm to use when storing tokens
    'HASH_ALGORITHM': 'sha256',
    # Number of PBKDF2 iterations (if you use PBKDF2)
    'HASH_ITERATIONS': 100_000,
    # Length of the random salt (in bytes)
    'SALT_LENGTH': 16,
    # Final stored token length (after hashing & encoding)
    'STORED_TOKEN_LENGTH': 64,
    # ─────────────────────────────────────────────────────────────
    # Expiry
    # ─────────────────────────────────────────────────────────────
    # Default token lifetime in days (None = never expires)
    'DEFAULT_EXPIRY_DAYS': 7,
    # If True, tokens automatically rotate (re-hash) on each use
    'ROTATE_ON_USE': False,
    # ─────────────────────────────────────────────────────────────
    # Scopes & Permissions
    # ─────────────────────────────────────────────────────────────
    # Allowed “scope” names (must map to your DRF permissions logic)
    'AVAILABLE_SCOPES': [
        'read',        # read-only access
        'write',       # modify resources
        'admin',       # superuser-level
        'audit',       # view audit logs only
    ],
    # Default scopes applied when none are specified
    'DEFAULT_SCOPES': ['read'],
    # DRF Permission class to enforce scopes (must implement `.has_permission`)
    'PERMISSION_CLASS': 'rest_framework.permissions.BasePermission',
    # The name of the field/key in the token model that holds scope list
    'SCOPE_FIELD_NAME': 'scopes',
    # ─────────────────────────────────────────────────────────────
    # Token modeling
    # ─────────────────────────────────────────────────────────────
    # Django model to use for storing your tokens
    'TOKEN_MODEL': 'keysmith.KeysmithToken',
    # If True, deleting a user will cascade-delete their tokens
    'CASCADE_ON_USER_DELETE': True,
    # ─────────────────────────────────────────────────────────────
    # Transmission & retrieval
    # ─────────────────────────────────────────────────────────────
    # Header name where clients send their token
    'HEADER_NAME': 'HTTP_X_KEYSMITH_TOKEN',
    # Enable reading token from a cookie as fallback
    'ALLOW_COOKIE': False,
    'COOKIE_NAME': 'keysmith_token',
    # Query-param fallback (e.g. ?token=…)
    'ALLOW_QUERY_PARAM': False,
    'QUERY_PARAM_NAME': 'keysmith_token',
    # ─────────────────────────────────────────────────────────────
    # Auditing & logging
    # ─────────────────────────────────────────────────────────────
    # Whether to log each token creation/usage
    'ENABLE_AUDIT_LOGGING': True,
    # Django model to use for audit records (if enabled)
    'AUDIT_LOG_MODEL': 'keysmith.KeysmithAuditLog',
}



class KeysmithSettings:
    def __init__(self, user_settings=None):
        if user_settings is not None:
            self._user_settings = user_settings
        self._cached_attrs = set()

    @property
    def user_settings(self):
        return getattr(settings, 'KEYSMITH', {})

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
        if hasattr(self, '_user_settings'):
            del self._user_settings

keysmith_settings = KeysmithSettings()

def _reload_keysmith_settings(*, setting, **kwargs):
    if setting == 'KEYSMITH':
        keysmith_settings.reload()

setting_changed.connect(_reload_keysmith_settings)
