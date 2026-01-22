from __future__ import annotations

import secrets
import string
import zlib
from typing import Tuple

_DICTIONARY = string.ascii_letters + string.digits


def generate_raw_secret(length: int = 32) -> str:
    return "".join(secrets.choice(_DICTIONARY) for _ in range(length))


def compute_crc(value: str, crc_digits: int = 6) -> str:
    crc = (
        zlib.crc32(value.encode("utf-8")) & 0xFFFFFFFF
    )  # bitwise shennanigans to convert to unsigned int just to be safe
    mod = 10**crc_digits
    return f"{crc % mod:0{crc_digits}d}"


def build_public_token(prefix: str, secret: str) -> str:
    """
    Construct the full public token string.

    Format:
        <prefix>_<secret><crc>
    """
    if not prefix:
        raise ValueError("Token prefix is required")

    body: str = f"{prefix}_{secret}"
    checksum: str = compute_crc(value=body)
    return f"{body}{checksum}"


def extract_prefix_and_secret(public_token: str) -> Tuple[str, str]:
    if not public_token:
        raise ValueError("Token is empty")

    crc_len: int = 6

    if len(public_token) <= crc_len + 2:
        # must at least fit the format p_<s><crc>
        raise ValueError("Token too short")

    body = public_token[:-crc_len]
    provided_crc = public_token[-crc_len:]
    expected_crc = compute_crc(body)

    if not secrets.compare_digest(provided_crc, expected_crc):
        raise ValueError("Invalid token checksum")

    if "_" not in body:
        raise ValueError("Invalid token format")

    prefix, secret = body.split("_", 1)

    if not prefix:
        raise ValueError("Missing token prefix")

    if not secret:
        raise ValueError("Missing token secret")

    return prefix, secret


def build_hint(secret: str) -> str:
    """
    Return a non-sensitive hint for display purposes.

    The hint is derived from the *end* of the secret to help humans
    visually distinguish tokens without exposing sensitive data.
    """
    if not secret:
        return ""

    hint_len: int = 8  # note: can be moved to configuration later if required

    if hint_len <= 0:
        return ""

    if len(secret) <= hint_len:
        return "…" + secret[-max(1, hint_len // 2) :]

    return f"…{secret[-hint_len:]}"
