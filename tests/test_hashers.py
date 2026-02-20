import pytest

from keysmith.hashers.base import BaseTokenHasher
from keysmith.hashers.pbkdf2 import PBKDF2SHA512TokenHasher
from keysmith.hashers.registry import get_hasher


class TestBaseTokenHasher:
    """Test base hasher functionality."""

    def test_base_hasher_is_abstract(self):
        """BaseTokenHasher cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTokenHasher()

    def test_base_hasher_requires_hash_method(self):
        """Concrete hasher must implement hash method."""

        class IncompleteHasher(BaseTokenHasher):
            def verify(self, secret: str, hashed: str) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteHasher()

    def test_base_hasher_requires_verify_method(self):
        """Concrete hasher must implement verify method."""

        class IncompleteHasher(BaseTokenHasher):
            def hash(self, secret: str) -> str:
                return "hashed"

        with pytest.raises(TypeError):
            IncompleteHasher()


class TestPBKDF2SHA512TokenHasher:
    """Test PBKDF2-SHA512 hasher."""

    def test_hasher_produces_pbkdf2_output(self):
        """Hasher produces PBKDF2 formatted output."""
        hasher = PBKDF2SHA512TokenHasher()
        secret = "test-secret-12345"

        hashed = hasher.hash(secret)

        assert hashed.startswith("pbkdf2_sha512$")

    def test_hasher_verifies_correct_secret(self):
        """Hasher verifies correct secret."""
        hasher = PBKDF2SHA512TokenHasher()
        secret = "test-secret-12345"

        hashed = hasher.hash(secret)

        assert hasher.verify(secret, hashed) is True

    def test_hasher_rejects_incorrect_secret(self):
        """Hasher rejects incorrect secret."""
        hasher = PBKDF2SHA512TokenHasher()
        secret = "test-secret-12345"
        wrong_secret = "wrong-secret-12345"

        hashed = hasher.hash(secret)

        assert hasher.verify(wrong_secret, hashed) is False

    def test_hasher_produces_different_hashes_for_same_secret(self):
        """Hasher produces different hashes for the same secret (due to salt)."""
        hasher = PBKDF2SHA512TokenHasher()
        secret = "test-secret-12345"

        hash1 = hasher.hash(secret)
        hash2 = hasher.hash(secret)

        assert hash1 != hash2
        # But both should verify
        assert hasher.verify(secret, hash1) is True
        assert hasher.verify(secret, hash2) is True

    def test_hasher_algorithm_name(self):
        """Hasher reports correct algorithm name."""
        hasher = PBKDF2SHA512TokenHasher()

        assert hasher.algorithm == "pbkdf2_sha512"


class TestHasherRegistry:
    """Test hasher registry."""

    def test_get_hasher_returns_default(self):
        """get_hasher returns default PBKDF2 hasher."""
        hasher = get_hasher()

        assert isinstance(hasher, PBKDF2SHA512TokenHasher)

    def test_get_hasher_returns_new_instance(self):
        """get_hasher returns a new instance each time."""
        hasher1 = get_hasher()
        hasher2 = get_hasher()

        # Not the same instance (no singleton)
        assert hasher1 is not hasher2
        # But same type
        assert type(hasher1) is type(hasher2)
