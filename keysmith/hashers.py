import base64
import hashlib
import os


class BaseTokenHasher:
    algorithm = None
    digest = None
    iterations = 1  # since entropy of token is high and performance is critical

    def encode(self, token, salt=None, iterations=None):
        if not salt:
            salt = base64.urlsafe_b64encode(os.urandom(16)).decode('ascii')
        iterations = iterations or self.iterations
        dk = hashlib.pbkdf2_hmac(
            self.digest().name,
            token.encode(),
            salt.encode(),
            iterations
        )
        hash = base64.urlsafe_b64encode(dk).decode('ascii')
        return f"{self.algorithm}${iterations}${salt}${hash}"

    def verify(self, token, encoded):
        algorithm, iterations, salt, hash = encoded.split('$', 3)
        encoded_2 = self.encode(token, salt, int(iterations))
        return encoded == encoded_2


class PBKDF2SHA256TokenHasher(BaseTokenHasher):
    algorithm = 'sha256'
    digest = hashlib.sha256


class PBKDF2SHA512TokenHasher(BaseTokenHasher):
    algorithm = 'sha512'
    digest = hashlib.sha512
