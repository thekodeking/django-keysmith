"""
Base hasher class for Keysmith tokens.

This class defines the interface and common helpers for token hashing,
salting, verification, and configuration-aware behavior.
"""

import hmac
import secrets
from abc import ABC, abstractmethod
from keysmith.settings import keysmith_settings


class BaseTokenHasher(ABC):
    """
    Abstract base class for all Keysmith token hashers.

    Subclasses must implement:
        - encode(key: str, salt: str) -> str
        - verify(key: str, hashed_key: str) -> bool
    """

    def __init__(self):
        self.iterations = keysmith_settings.HASH_ITERATIONS
        self.salt_length = keysmith_settings.SALT_LENGTH

    def generate_salt(self) -> str:
        """
        Generate a cryptographically secure random salt.
        """
        return secrets.token_hex(self.salt_length)

    @abstractmethod
    def encode(self, key: str, salt: str, iterations: int) -> str:
        """
        Hashes the token using the salt and returns a string representation.
        """
        pass

    @abstractmethod
    def verify(self, key: str, hashed_key: str) -> bool:
        """
        Returns True if the provided key matches the hashed key.
        """
        pass

    def safe_compare(self, a: str, b: str) -> bool:
        """
        Constant-time comparison to prevent timing attacks.
        """
        return hmac.compare_digest(a, b)
