from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework.throttling import SimpleRateThrottle
except ImportError as exc:
    raise ImproperlyConfigured(
        "Keysmith DRF throttling requires installing django-keysmith[drf]."
    ) from exc


class KeysmithTokenRateThrottle(SimpleRateThrottle):
    """
    Throttle requests based on the authenticated Keysmith token prefix.

    Falls back to client IP address for unauthenticated requests.

    Usage:
        In views:
            class MyAPIView(APIView):
                throttle_classes = [KeysmithTokenRateThrottle]

        In settings.py:
            REST_FRAMEWORK = {
                "DEFAULT_THROTTLE_CLASSES": [
                    "keysmith.drf.throttling.KeysmithTokenRateThrottle",
                ],
                "DEFAULT_THROTTLE_RATES": {
                    "keysmith_token": "1000/hour",
                },
            }
    """

    scope = "keysmith_token"
    rate = "1000/hour"

    def get_rate(self):
        try:
            return super().get_rate()
        except ImproperlyConfigured:
            return self.rate

    def get_cache_key(self, request, view):
        token = getattr(request, "auth", None)
        if token is not None and hasattr(token, "prefix"):
            return self.cache_format % {
                "scope": self.scope,
                "ident": token.prefix,
            }

        # Fall back to client IP for unauthenticated requests
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
