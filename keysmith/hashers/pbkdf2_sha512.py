import hashlib
from keysmith.hashers.base import BaseTokenHasher


class PBKDF2SHA512TokenHasher(BaseTokenHasher):
    algorithm = "pbkdf2_sha512"
    iterations = 100000

    def encode(self, key: str, salt: str, iterations: int) -> str:
        key_bytes = key.encode()
        salt_bytes = salt.encode()

        derived_key = hashlib.pbkdf2_hmac(
            "sha512", key_bytes, salt_bytes, self.iterations
        )
        return f"{self.algorithm}${self.iterations}${salt}${derived_key.hex()}"

    def verify(self, key: str, hashed_key: str) -> bool:
        try:
            algorithm, iterations, salt, digest = hashed_key.split("$")
            assert algorithm == self.algorithm
        except (ValueError, AssertionError):
            return False

        encoded = self.encode(key, salt, int(iterations))
        return self.safe_compare(encoded, hashed_key)
