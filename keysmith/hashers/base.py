from abc import ABC, abstractmethod


class BaseTokenHasher(ABC):
    """
    Base interface for token hashers.
    """

    @abstractmethod
    def hash(self, secret: str) -> str:
        """
        Hash a raw token secret.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(self, secret: str, hashed: str) -> bool:
        """
        Verify a raw token secret against a stored hash.
        """
        raise NotImplementedError
