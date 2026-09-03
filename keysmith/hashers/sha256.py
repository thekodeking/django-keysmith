import hashlib
import hmac
import secrets

from django.conf import settings

from .base import BaseTokenHasher


class SHA256TokenHasher(BaseTokenHasher):
    """
    High-performance SHA-256 token hasher with random salt.

    Suitable for high-entropy API tokens (e.g. 32-character cryptographically
    random secrets with ~190 bits of entropy) where PBKDF2 iterations
    would introduce unnecessary latency and CPU overhead on high-throughput services.
    """

    algorithm = "sha256"

    def hash(self, secret: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.sha256(f"{salt}{secret}".encode()).hexdigest()
        return f"{self.algorithm}${salt}${digest}"

    def verify(self, secret: str, hashed: str) -> bool:
        try:
            algorithm, salt, digest = hashed.split("$", 2)
        except ValueError:
            return False

        if algorithm != self.algorithm:
            return False

        expected = hashlib.sha256(f"{salt}{secret}".encode()).hexdigest()
        return secrets.compare_digest(expected, digest)


class HMACSHA256TokenHasher(BaseTokenHasher):
    """
    Keyed HMAC-SHA256 token hasher using Django SECRET_KEY.

    Provides sub-millisecond cryptographic verification with tamper-evident
    keyed hashing.
    """

    algorithm = "hmac_sha256"

    def __init__(self, key: str | bytes | None = None):
        if key is None:
            key = settings.SECRET_KEY
        if isinstance(key, str):
            key = key.encode("utf-8")
        self._key = key

    def hash(self, secret: str) -> str:
        salt = secrets.token_hex(16)
        mac = hmac.new(self._key, f"{salt}{secret}".encode(), hashlib.sha256).hexdigest()
        return f"{self.algorithm}${salt}${mac}"

    def verify(self, secret: str, hashed: str) -> bool:
        try:
            algorithm, salt, mac = hashed.split("$", 2)
        except ValueError:
            return False

        if algorithm != self.algorithm:
            return False

        expected = hmac.new(self._key, f"{salt}{secret}".encode(), hashlib.sha256).hexdigest()
        return secrets.compare_digest(expected, mac)
