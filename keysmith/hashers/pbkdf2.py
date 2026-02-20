import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher

from keysmith.settings import keysmith_settings

from .base import BaseTokenHasher


class PBKDF2SHA512TokenHasher(BaseTokenHasher):
    """
    PBKDF2-SHA512 hasher for keysmith tokens.
    """

    algorithm = "pbkdf2_sha512"

    def __init__(self):
        self._hasher = PBKDF2PasswordHasher()
        self._hasher.iterations = keysmith_settings.HASH_ITERATIONS
        self._hasher.algorithm = self.algorithm
        self._hasher.digest = hashlib.sha512

    def hash(self, secret: str) -> str:
        return self._hasher.encode(
            password=secret,
            salt=self._hasher.salt(),
        )

    def verify(self, secret: str, hashed: str) -> bool:
        return self._hasher.verify(secret, hashed)
